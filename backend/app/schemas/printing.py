"""Pydantic schemas for the thermal-printing endpoints."""

from pydantic import BaseModel, Field


class BadgePrintRequest(BaseModel):
    """Payload to print a visitor badge via the server's template.

    Attributes:
        name (str): Person name (required by the template).
        company (str | None): Optional company line.
        qr_data (str | None): Optional URL/text encoded as a QR code.
        copies (int): Number of copies (1-100).
    """

    name: str = Field(min_length=1, max_length=80)
    company: str | None = None
    qr_data: str | None = None
    copies: int = Field(default=1, ge=1, le=100)


class PrinterStatus(BaseModel):
    """Read-only printer configuration and reachability for the settings page.

    The API key itself is never included — only whether one is configured.

    Attributes:
        base_url (str): Configured print server base URL.
        key_configured (bool): Whether ``SLP650_API_KEY`` is set.
        ok (bool | None): Printer readiness; ``None`` when unreachable.
        error (str | None): Readable error when the server can't be reached.
    """

    base_url: str
    key_configured: bool
    ok: bool | None = None
    error: str | None = None


class LocationLabelPrintRequest(BaseModel):
    """Payload to print a location label rendered by this app.

    Attributes:
        qr_base_url (str | None): Origin the QR should point at (the frontend
            sends its own origin). Ignored when ``INV_PUBLIC_BASE_URL`` is set.
        copies (int): Number of copies (1-100).
    """

    qr_base_url: str | None = Field(default=None, max_length=200)
    copies: int = Field(default=1, ge=1, le=100)
