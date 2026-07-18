"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend.

    Attributes:
        app_name (str): Human-readable application name.
        database_url (str): Async SQLAlchemy database URL.
        cors_origins (list[str]): Allowed browser origins for CORS.
        media_dir (str): Filesystem directory where uploaded images are stored.
        media_url (str): URL prefix under which stored images are served.
        slp650_base_url (str): Base URL of the SLP650 print server (REST agent).
        slp650_api_key (str): API key for the print server. Server-side only —
            must never be exposed to browser code.
        app_pin (str): Seed for the access PIN on first boot; the stored
            (hashed) PIN in the database takes precedence afterwards.
        public_base_url (str): Canonical origin users reach the app at, e.g.
            ``"http://10.0.0.228:8080"``. When set, printed QR codes always
            use it instead of the printing browser's own origin.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INV_", extra="ignore")

    app_name: str = "Inventário Doméstico"
    database_url: str = "sqlite+aiosqlite:///./inventory.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    media_dir: str = "./media"
    media_url: str = "/media"
    slp650_base_url: str = Field(
        default="http://100.87.166.24:8787", validation_alias="SLP650_BASE_URL"
    )
    slp650_api_key: str = Field(default="", validation_alias="SLP650_API_KEY")
    app_pin: str = ""
    public_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance.

    Returns:
        Settings: The process-wide settings singleton.
    """
    return Settings()
