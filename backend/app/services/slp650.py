"""Typed async client for the SLP650 print server (slp650-sdk REST agent).

The print server runs next to the printer (Raspberry Pi) and is documented in
``~/Documents/dev/slp650-sdk/docs/07_REST_API.md``. All calls happen server-side
so the API key never reaches the browser.
"""

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.services.errors import NotFoundError, ServiceError


class PrinterUnavailableError(ServiceError):
    """Raised when the print server or the printer cannot take the job."""

    status_code = 503


class PrintRequestError(ServiceError):
    """Raised when the print server rejects the request parameters."""

    status_code = 422


class PrintServerHealth(BaseModel):
    """Health report from the print server.

    Attributes:
        ok (bool): ``True`` when the printer is present and ready.
    """

    model_config = ConfigDict(extra="allow")

    ok: bool


class TemplateInfo(BaseModel):
    """A label template registered on the print server.

    Attributes:
        name (str): Template identifier used in print calls.
        description (str): Human-readable description.
        default_media (str): Media the template targets by default.
        required_fields (list[str]): Fields that must be provided.
        optional_fields (list[str]): Fields that may be provided.
    """

    model_config = ConfigDict(extra="allow")

    name: str
    description: str = ""
    default_media: str = ""
    required_fields: list[str] = []
    optional_fields: list[str] = []


class PrintResult(BaseModel):
    """Outcome of a print call.

    Attributes:
        engine (str): Encoder used by the server (``native`` or ``cups``).
    """

    model_config = ConfigDict(extra="allow")

    engine: str = ""


class Slp650Client:
    """Async client wrapping the SLP650 REST endpoints used by this app."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Initialize the client from settings or explicit values.

        Args:
            base_url (str | None): Print server base URL; defaults to settings.
            api_key (str | None): API key; defaults to settings.
            timeout (float): Request timeout in seconds.
            transport (httpx.AsyncBaseTransport | None): Optional transport,
                used by tests to mock the server.
        """
        settings = get_settings()
        self.base_url = (base_url or settings.slp650_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.slp650_api_key
        self.timeout = timeout
        self.transport = transport

    async def health(self) -> PrintServerHealth:
        """Return the print server's health report.

        Returns:
            PrintServerHealth: Printer availability and server details.
        """
        return PrintServerHealth.model_validate(await self._request("GET", "/health"))

    async def templates(self) -> list[TemplateInfo]:
        """List the templates registered on the print server.

        Returns:
            list[TemplateInfo]: Available templates with their field contracts.
        """
        payload = await self._request("GET", "/templates")
        return [TemplateInfo.model_validate(entry) for entry in payload]

    async def print_template(
        self,
        template: str,
        fields: dict[str, str],
        media: str | None = None,
        copies: int = 1,
    ) -> PrintResult:
        """Print a server-side template from field values.

        Args:
            template (str): Template name, e.g. ``"visitor-badge"``.
            fields (dict[str, str]): Field values required by the template.
            media (str | None): Media override; template default when ``None``.
            copies (int): Number of copies (1-100).

        Returns:
            PrintResult: The print outcome.
        """
        body: dict[str, Any] = {"template": template, "fields": fields, "copies": copies}
        if media is not None:
            body["media"] = media
        payload = await self._request("POST", "/print/template", json=body)
        return PrintResult.model_validate(payload)

    async def print_image(
        self,
        data: bytes,
        filename: str = "label.png",
        content_type: str = "image/png",
        media: str = "MediaBadge",
        copies: int = 1,
    ) -> PrintResult:
        """Print an image, fitted by the server onto the media canvas.

        Args:
            data (bytes): Image bytes (PNG or JPEG, max 20 MiB).
            filename (str): Filename reported in the multipart upload.
            content_type (str): MIME type of the image.
            media (str): Target media name, e.g. ``"MediaBadge"``.
            copies (int): Number of copies (1-100).

        Returns:
            PrintResult: The print outcome.
        """
        payload = await self._request(
            "POST",
            "/print/image",
            files={"file": (filename, data, content_type)},
            data={"media": media, "copies": str(copies)},
        )
        return PrintResult.model_validate(payload)

    async def print_text(
        self, text: str, media: str = "MediaBadge", copies: int = 1
    ) -> PrintResult:
        """Print plain text rendered by the server.

        Args:
            text (str): Text to print.
            media (str): Target media name.
            copies (int): Number of copies (1-100).

        Returns:
            PrintResult: The print outcome.
        """
        body = {"text": text, "media": media, "copies": copies}
        payload = await self._request("POST", "/print/text", json=body)
        return PrintResult.model_validate(payload)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send a request and translate transport/HTTP failures to domain errors.

        Args:
            method (str): HTTP method.
            path (str): Endpoint path, e.g. ``"/health"``.
            **kwargs (Any): Extra arguments passed to ``httpx.AsyncClient.request``.

        Returns:
            Any: The decoded JSON payload.

        Raises:
            PrinterUnavailableError: If the key is missing/invalid, the server is
                unreachable, or the printer is offline (503).
            PrintRequestError: If the server rejects the parameters (413/422).
            NotFoundError: If a template name is unknown (404).
        """
        if not self.api_key:
            raise PrinterUnavailableError(
                "SLP650_API_KEY não configurada no servidor. "
                "Defina a variável de ambiente e reinicie o backend."
            )
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-API-Key": self.api_key},
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise PrinterUnavailableError(
                f"Servidor de impressão inacessível em {self.base_url}. "
                "Verifique a rede (Tailscale) e o serviço no Raspberry Pi."
            ) from exc
        if response.is_success:
            return response.json()
        raise self._translate_error(response)

    def _translate_error(self, response: httpx.Response) -> ServiceError:
        """Map an error response from the print server to a domain error.

        Args:
            response (httpx.Response): The non-2xx response.

        Returns:
            ServiceError: The domain error to raise.
        """
        detail = self._detail(response)
        match response.status_code:
            case 401:
                return PrinterUnavailableError(
                    "Servidor de impressão recusou a chave de API (SLP650_API_KEY)."
                )
            case 404:
                return NotFoundError(f"Modelo de etiqueta desconhecido no servidor: {detail}")
            case 413:
                return PrintRequestError("Imagem maior que 20 MiB.")
            case 422:
                return PrintRequestError(f"Servidor de impressão rejeitou os parâmetros: {detail}")
            case 503:
                return PrinterUnavailableError(
                    f"Impressora offline ou indisponível: {detail}"
                )
            case _:
                return PrinterUnavailableError(
                    f"Erro inesperado do servidor de impressão ({response.status_code}): {detail}"
                )

    @staticmethod
    def _detail(response: httpx.Response) -> str:
        """Extract a readable detail message from an error response.

        Args:
            response (httpx.Response): The error response.

        Returns:
            str: The ``detail`` field, or the raw body as fallback.
        """
        try:
            detail = response.json().get("detail", "")
        except (ValueError, AttributeError):
            detail = ""
        if isinstance(detail, list):
            detail = "; ".join(str(entry.get("msg", entry)) for entry in detail)
        return str(detail) or response.text[:200]
