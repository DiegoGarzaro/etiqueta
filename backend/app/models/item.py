"""Item ORM model — a physical thing stored in exactly one location."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import item_category
from app.models.base import UUIDAuditBase

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.location import Location
    from app.models.photo import Photo


class Item(UUIDAuditBase):
    """A catalogued object stored in a single location.

    Attributes:
        name (str): Item name, e.g. "Carregador USB-C".
        description (str | None): Longer description.
        quantity (int): How many of this item are stored (default 1).
        location_id (str): Owning location id.
        notes (str | None): Free-form notes.
        search_text (str): Accent-insensitive text used for search.
        location (Location): The location holding this item.
        categories (list[Category]): Categories tagged on this item.
    """

    __tablename__ = "item"

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location_id: Mapped[str] = mapped_column(
        ForeignKey("location.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_text: Mapped[str] = mapped_column(String(400), nullable=False, default="", index=True)

    location: Mapped[Location] = relationship(back_populates="items", lazy="selectin")
    categories: Mapped[list[Category]] = relationship(
        secondary=item_category, back_populates="items", lazy="selectin"
    )
    photos: Mapped[list[Photo]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Photo.created_at",
        lazy="selectin",
    )
