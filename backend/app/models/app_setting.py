"""Key-value application settings persisted in the database."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AppSetting(Base):
    """A single persisted setting (e.g. the access PIN hash).

    Attributes:
        key (str): Setting name.
        value (str): Setting value.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
