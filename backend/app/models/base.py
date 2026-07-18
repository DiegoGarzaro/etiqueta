"""Declarative base and shared mixins for ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def generate_uuid() -> str:
    """Generate a random UUID4 string primary key.

    Returns:
        str: A new UUID4 formatted as a 36-character string.
    """
    return str(uuid.uuid4())


class UUIDAuditBase(Base):
    """Abstract base adding a UUID primary key and audit timestamps.

    Attributes:
        id (str): UUID4 primary key.
        created_at (datetime): Row creation timestamp.
        updated_at (datetime): Timestamp of the last update.
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
