"""Pydantic schemas for items."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead
from app.schemas.location import PathSegment
from app.schemas.photo import PhotoRead


class LocationSummary(BaseModel):
    """Compact location reference embedded in item responses.

    Attributes:
        id (str): Location id.
        name (str): Location name.
        code (str): Own code segment.
        full_code (str): Joined ancestor codes for the tag.
        path (list[PathSegment]): Ancestors from root to the location.
    """

    id: str
    name: str
    code: str
    full_code: str
    path: list[PathSegment] = []


class ItemBase(BaseModel):
    """Shared item fields.

    Attributes:
        name (str): Item name.
        description (str | None): Longer description.
        quantity (int): Stored quantity (>= 0).
        notes (str | None): Free-form notes.
    """

    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    quantity: int = Field(default=1, ge=0)
    notes: str | None = None


class ItemCreate(ItemBase):
    """Payload to create an item.

    Attributes:
        location_id (str): Location the item is stored in.
        category_ids (list[str]): Categories to tag on the item.
    """

    location_id: str
    category_ids: list[str] = []


class ItemUpdate(BaseModel):
    """Payload to partially update an item.

    Attributes:
        name (str | None): New name, if changing.
        description (str | None): New description, if changing.
        quantity (int | None): New quantity, if changing.
        notes (str | None): New notes, if changing.
        location_id (str | None): New location, if moving.
        category_ids (list[str] | None): Full replacement set of categories.
    """

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    notes: str | None = None
    location_id: str | None = None
    category_ids: list[str] | None = None


class ItemRead(ItemBase):
    """Item as returned by the API.

    Attributes:
        id (str): Item id.
        location (LocationSummary): Where the item is stored.
        categories (list[CategoryRead]): Tagged categories.
        photos (list[PhotoRead]): Attached photos, oldest first.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    location: LocationSummary
    categories: list[CategoryRead] = []
    photos: list[PhotoRead] = []
