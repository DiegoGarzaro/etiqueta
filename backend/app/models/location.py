"""Location ORM model — a place that holds items or other locations."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDAuditBase

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.photo import Photo


class LocationType(enum.StrEnum):
    """Physical type of a storage location (Portuguese vocabulary)."""

    COMODO = "comodo"
    ARMARIO = "armario"
    GAVETA = "gaveta"
    PRATELEIRA = "prateleira"
    CAIXA = "caixa"
    ORGANIZADOR = "organizador"


class Location(UUIDAuditBase):
    """A node in the storage tree (cômodo, armário, gaveta, caixa, ...).

    Attributes:
        name (str): Human name, e.g. "Armário A".
        type (LocationType): Physical type of the location.
        parent_id (str | None): Parent location id; ``None`` for a root cômodo.
        code (str): Own label segment, e.g. "ARM-A" or "GAV-02".
        search_text (str): Accent-insensitive text used for search.
        notes (str | None): Free-form notes.
        parent (Location | None): Parent location.
        children (list[Location]): Direct child locations.
        items (list[Item]): Items stored directly in this location.
    """

    __tablename__ = "location"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("location.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    search_text: Mapped[str] = mapped_column(String(280), nullable=False, default="", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[Location | None] = relationship(
        back_populates="children", remote_side="Location.id"
    )
    children: Mapped[list[Location]] = relationship(
        back_populates="parent", cascade="all, delete-orphan", passive_deletes=True
    )
    items: Mapped[list[Item]] = relationship(
        back_populates="location", cascade="all, delete-orphan", passive_deletes=True
    )
    photos: Mapped[list[Photo]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Photo.created_at",
        lazy="selectin",
    )
