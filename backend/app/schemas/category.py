"""Pydantic schemas for categories."""

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Shared category fields.

    Attributes:
        name (str): Category name.
        color (str): Hex color for the chip.
        icon (str | None): Optional icon identifier.
    """

    name: str = Field(min_length=1, max_length=80)
    color: str = Field(default="#5B6670", max_length=9)
    icon: str | None = Field(default=None, max_length=40)


class CategoryCreate(CategoryBase):
    """Payload to create a category."""


class CategoryUpdate(BaseModel):
    """Payload to partially update a category.

    Attributes:
        name (str | None): New name, if changing.
        color (str | None): New color, if changing.
        icon (str | None): New icon, if changing.
    """

    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=9)
    icon: str | None = Field(default=None, max_length=40)


class CategoryRead(CategoryBase):
    """Category as returned by the API.

    Attributes:
        id (str): Category id.
        item_count (int): Number of items tagged with this category.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    item_count: int = 0
