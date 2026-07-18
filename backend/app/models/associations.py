"""Association tables for many-to-many relationships."""

from sqlalchemy import Column, ForeignKey, Table

from app.models.base import Base

item_category = Table(
    "item_category",
    Base.metadata,
    Column("item_id", ForeignKey("item.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("category.id", ondelete="CASCADE"), primary_key=True),
)
"""Links items to their categories (many-to-many)."""
