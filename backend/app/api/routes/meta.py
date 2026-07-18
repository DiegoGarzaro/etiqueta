"""App configuration exposed to the frontend."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["meta"])


class AppConfig(BaseModel):
    """Frontend-relevant configuration.

    Attributes:
        public_base_url (str | None): Canonical origin for printed QR codes,
            or ``None`` to use the browser's own origin.
    """

    public_base_url: str | None


@router.get("/config", response_model=AppConfig)
async def app_config() -> AppConfig:
    """Return the frontend-relevant configuration.

    Returns:
        AppConfig: The current configuration.
    """
    return AppConfig(public_base_url=get_settings().public_base_url or None)
