"""Pydantic schemas for full-inventory export and import."""

from pydantic import BaseModel, Field

from app.models.location import LocationType


class BackupCategory(BaseModel):
    """A category in a backup file."""

    id: str
    name: str
    color: str
    icon: str | None = None


class BackupLocation(BaseModel):
    """A location in a backup file."""

    id: str
    name: str
    type: LocationType
    parent_id: str | None = None
    code: str
    notes: str | None = None


class BackupItem(BaseModel):
    """An item in a backup file, with its category ids."""

    id: str
    name: str
    description: str | None = None
    quantity: int = 1
    notes: str | None = None
    location_id: str
    category_ids: list[str] = []


class BackupPhoto(BaseModel):
    """A photo's metadata in a backup file (image files are backed up separately)."""

    id: str
    item_id: str | None = None
    location_id: str | None = None
    filename: str
    thumb_filename: str
    content_type: str
    width: int
    height: int


class BackupData(BaseModel):
    """A complete inventory snapshot.

    Attributes:
        version (int): Backup format version.
        exported_at (str): ISO timestamp of the export.
        categories (list[BackupCategory]): All categories.
        locations (list[BackupLocation]): All locations.
        items (list[BackupItem]): All items.
        photos (list[BackupPhoto]): All photo metadata.
    """

    version: int = 1
    exported_at: str = ""
    categories: list[BackupCategory] = Field(default_factory=list)
    locations: list[BackupLocation] = Field(default_factory=list)
    items: list[BackupItem] = Field(default_factory=list)
    photos: list[BackupPhoto] = Field(default_factory=list)


class ImportResult(BaseModel):
    """Counts of records restored by an import.

    Attributes:
        categories (int): Categories inserted.
        locations (int): Locations inserted.
        items (int): Items inserted.
        photos (int): Photo rows inserted.
    """

    categories: int
    locations: int
    items: int
    photos: int
