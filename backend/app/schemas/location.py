"""Pydantic schemas for locations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.location import LocationType
from app.schemas.photo import PhotoRead


class PathSegment(BaseModel):
    """One ancestor step in a location's path.

    Attributes:
        id (str): Location id.
        name (str): Location name.
        code (str): Location code segment.
    """

    id: str
    name: str
    code: str


class LocationBase(BaseModel):
    """Shared location fields.

    Attributes:
        name (str): Location name.
        type (LocationType): Physical type.
        parent_id (str | None): Parent id, or ``None`` for a root cômodo.
        notes (str | None): Free-form notes.
    """

    name: str = Field(min_length=1, max_length=120)
    type: LocationType
    parent_id: str | None = None
    notes: str | None = None


class LocationCreate(LocationBase):
    """Payload to create a location."""


class LocationUpdate(BaseModel):
    """Payload to partially update a location.

    Attributes:
        name (str | None): New name, if changing.
        parent_id (str | None): New parent, if moving.
        notes (str | None): New notes, if changing.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: str | None = None
    notes: str | None = None


class LocationRead(BaseModel):
    """Location as returned by the API, with computed code and path.

    Attributes:
        id (str): Location id.
        name (str): Location name.
        type (LocationType): Physical type.
        parent_id (str | None): Parent id.
        code (str): Own code segment, e.g. "GAV-02".
        full_code (str): Joined ancestor codes, e.g. "ARM-A · GAV-02".
        path (list[PathSegment]): Ancestors from root to this location.
        notes (str | None): Free-form notes.
        direct_item_count (int): Items stored directly here.
        total_item_count (int): Items here and in all descendants.
        photos (list[PhotoRead]): Attached photos, oldest first.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: LocationType
    parent_id: str | None
    code: str
    full_code: str
    path: list[PathSegment] = []
    notes: str | None = None
    direct_item_count: int = 0
    total_item_count: int = 0
    photos: list[PhotoRead] = []


class LocationTreeNode(LocationRead):
    """A location plus its nested children, for the tree browser.

    Attributes:
        children (list[LocationTreeNode]): Nested child locations.
    """

    children: list[LocationTreeNode] = []
