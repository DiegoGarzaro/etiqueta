"""Photo ORM model — an image attached to an item or a location."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDAuditBase

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.location import Location


class Photo(UUIDAuditBase):
    """An uploaded image belonging to exactly one item or one location.

    Attributes:
        item_id (str | None): Owning item id, if attached to an item.
        location_id (str | None): Owning location id, if attached to a location.
        filename (str): Stored filename of the web-sized image.
        thumb_filename (str): Stored filename of the thumbnail.
        content_type (str): MIME type of the stored image.
        width (int): Width of the web-sized image in pixels.
        height (int): Height of the web-sized image in pixels.
        item (Item | None): The owning item.
        location (Location | None): The owning location.
    """

    __tablename__ = "photo"

    item_id: Mapped[str | None] = mapped_column(
        ForeignKey("item.id", ondelete="CASCADE"), nullable=True, index=True
    )
    location_id: Mapped[str | None] = mapped_column(
        ForeignKey("location.id", ondelete="CASCADE"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(80), nullable=False)
    thumb_filename: Mapped[str] = mapped_column(String(80), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False, default="image/jpeg")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped[Item | None] = relationship(back_populates="photos")
    location: Mapped[Location | None] = relationship(back_populates="photos")
