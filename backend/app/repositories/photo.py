"""Data access for photos."""

from app.models.photo import Photo
from app.repositories.base import BaseRepository


class PhotoRepository(BaseRepository[Photo]):
    """Repository for :class:`~app.models.photo.Photo`."""

    model = Photo
