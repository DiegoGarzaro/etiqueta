"""Thermal-printing endpoints proxying the SLP650 print server.

The browser never talks to the print server directly — the API key stays in
backend environment variables and every call goes through these routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.schemas.printing import BadgePrintRequest, LocationLabelPrintRequest, PrinterStatus
from app.services.errors import ServiceError
from app.services.label_image import render_location_label
from app.services.location import LocationService
from app.services.slp650 import (
    PrintRequestError,
    PrintResult,
    PrintServerHealth,
    Slp650Client,
    TemplateInfo,
)

router = APIRouter(prefix="/print", tags=["print"])

_IMAGE_TYPES = {"image/png", "image/jpeg"}
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def get_print_client() -> Slp650Client:
    """Provide the SLP650 client configured from settings.

    Returns:
        Slp650Client: The client instance (tests override this dependency).
    """
    return Slp650Client()


PrintClientDep = Annotated[Slp650Client, Depends(get_print_client)]


@router.get("/health", response_model=PrintServerHealth)
async def printer_health(client: PrintClientDep) -> PrintServerHealth:
    """Report whether the print server and printer are ready.

    Args:
        client (PrintClientDep): The SLP650 client.

    Returns:
        PrintServerHealth: The server's health payload.
    """
    return await client.health()


@router.get("/status", response_model=PrinterStatus)
async def printer_status(client: PrintClientDep) -> PrinterStatus:
    """Report printer configuration and reachability (never the API key).

    Args:
        client (PrintClientDep): The SLP650 client.

    Returns:
        PrinterStatus: Base URL, whether a key is set, and health or error.
    """
    status = PrinterStatus(base_url=client.base_url, key_configured=bool(client.api_key))
    try:
        status.ok = (await client.health()).ok
    except ServiceError as exc:
        status.error = str(exc)
    return status


@router.get("/templates", response_model=list[TemplateInfo])
async def list_templates(client: PrintClientDep) -> list[TemplateInfo]:
    """List label templates registered on the print server.

    Args:
        client (PrintClientDep): The SLP650 client.

    Returns:
        list[TemplateInfo]: Available templates.
    """
    return await client.templates()


@router.post("/badge", response_model=PrintResult)
async def print_badge(data: BadgePrintRequest, client: PrintClientDep) -> PrintResult:
    """Print a visitor badge using the server's ``visitor-badge`` template.

    Args:
        data (BadgePrintRequest): Badge fields and copy count.
        client (PrintClientDep): The SLP650 client.

    Returns:
        PrintResult: The print outcome.
    """
    fields = {"name": data.name}
    if data.company:
        fields["company"] = data.company
    if data.qr_data:
        fields["qr_data"] = data.qr_data
    return await client.print_template("visitor-badge", fields, copies=data.copies)


@router.post("/image", response_model=PrintResult)
async def print_image(
    file: UploadFile,
    client: PrintClientDep,
    copies: Annotated[int, Form(ge=1, le=100)] = 1,
) -> PrintResult:
    """Print an uploaded image, fitted onto the badge media by the server.

    Args:
        file (UploadFile): PNG or JPEG image (max 20 MiB).
        client (PrintClientDep): The SLP650 client.
        copies (int): Number of copies (1-100).

    Returns:
        PrintResult: The print outcome.

    Raises:
        PrintRequestError: If the upload is not a PNG/JPEG or is too large.
    """
    if file.content_type not in _IMAGE_TYPES:
        raise PrintRequestError("Envie uma imagem PNG ou JPEG.")
    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise PrintRequestError("Imagem maior que 20 MiB.")
    if not data:
        raise PrintRequestError("Arquivo de imagem vazio.")
    return await client.print_image(
        data,
        filename=file.filename or "label.png",
        content_type=file.content_type or "image/png",
        copies=copies,
    )


@router.post("/locations/{location_id}", response_model=PrintResult)
async def print_location_label(
    location_id: str,
    data: LocationLabelPrintRequest,
    session: SessionDep,
    client: PrintClientDep,
) -> PrintResult:
    """Render a location label and print it on the badge media.

    Args:
        location_id (str): The location id.
        data (LocationLabelPrintRequest): QR base URL and copy count.
        session (SessionDep): Database session.
        client (PrintClientDep): The SLP650 client.

    Returns:
        PrintResult: The print outcome.
    """
    png = await _render_label(session, location_id, data.qr_base_url)
    return await client.print_image(png, filename=f"{location_id}.png", copies=data.copies)


@router.get("/locations/{location_id}/preview.png")
async def preview_location_label(
    location_id: str, session: SessionDep, qr_base_url: str | None = None
) -> Response:
    """Return the rendered label as a PNG, exactly as it would print.

    Args:
        location_id (str): The location id.
        session (SessionDep): Database session.
        qr_base_url (str | None): Origin the QR should point at; ignored when
            ``INV_PUBLIC_BASE_URL`` is configured.

    Returns:
        Response: The 750x567 1-bit PNG preview.
    """
    png = await _render_label(session, location_id, qr_base_url)
    return Response(content=png, media_type="image/png")


def _resolve_qr_base(qr_base_url: str | None) -> str:
    """Pick the origin printed QR codes point at.

    ``INV_PUBLIC_BASE_URL`` wins so every label carries the canonical address
    no matter which origin the printing browser used.

    Args:
        qr_base_url (str | None): Origin sent by the frontend.

    Returns:
        str: The origin to encode, without a trailing slash.

    Raises:
        PrintRequestError: If neither the setting nor the request provides one.
    """
    base = get_settings().public_base_url or qr_base_url
    if not base:
        raise PrintRequestError("Nenhum endereço para o QR (defina INV_PUBLIC_BASE_URL).")
    return base.rstrip("/")


async def _render_label(
    session: SessionDep, location_id: str, qr_base_url: str | None
) -> bytes:
    """Fetch a location and render its label PNG.

    Args:
        session (SessionDep): Database session.
        location_id (str): The location id.
        qr_base_url (str | None): Origin sent by the frontend, if any.

    Returns:
        bytes: The rendered PNG.
    """
    location = await LocationService(session).get(location_id)
    qr_url = f"{_resolve_qr_base(qr_base_url)}/locais/{location.id}"
    return render_location_label(location.full_code, location.name, location.type, qr_url)
