"""Category ORM model — a cross-cutting tag for items."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import item_category
from app.models.base import UUIDAuditBase

if TYPE_CHECKING:
    from app.models.item import Item


class Category(UUIDAuditBase):
    """A label applied to items independently of their location.

    Attributes:
        name (str): Unique category name, e.g. "Eletrônicos".
        color (str): Hex color used for the category chip.
        icon (str | None): Optional icon identifier.
        items (list[Item]): Items tagged with this category.
    """

    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#5B6670")
    icon: Mapped[str | None] = mapped_column(String(40), nullable=True)

    items: Mapped[list[Item]] = relationship(
        secondary=item_category, back_populates="categories"
    )
