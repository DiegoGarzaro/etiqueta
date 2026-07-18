"""Business logic for photos attached to items and locations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.photo import Photo
from app.repositories.item import ItemRepository
from app.repositories.location import LocationRepository
from app.repositories.photo import PhotoRepository
from app.schemas.photo import PhotoRead
from app.services.errors import NotFoundError, ValidationError
from app.services.storage import ImageDecodeError, StorageService


def to_photo_read(photo: Photo, settings: Settings | None = None) -> PhotoRead:
    """Map a photo entity to its read schema with public URLs.

    Args:
        photo (Photo): The photo entity.
        settings (Settings | None): Settings for the media URL prefix.

    Returns:
        PhotoRead: The photo with ``url`` and ``thumb_url`` populated.
    """
    base = (settings or get_settings()).media_url.rstrip("/")
    return PhotoRead(
        id=photo.id,
        url=f"{base}/{photo.filename}",
        thumb_url=f"{base}/{photo.thumb_filename}",
        content_type=photo.content_type,
        width=photo.width,
        height=photo.height,
    )


class PhotoService:
    """Attach photos to items or locations and delete them."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.repository = PhotoRepository(session)
        self.items = ItemRepository(session)
        self.locations = LocationRepository(session)
        self.storage = StorageService(get_settings().media_dir)

    async def add_to_item(self, item_id: str, data: bytes) -> PhotoRead:
        """Store a photo and attach it to an item.

        Args:
            item_id (str): The owning item id.
            data (bytes): Raw uploaded image bytes.

        Returns:
            PhotoRead: The created photo.

        Raises:
            NotFoundError: If the item does not exist.
            ValidationError: If the bytes are not a valid image.
        """
        if await self.items.get(item_id) is None:
            raise NotFoundError("Item não encontrado.")
        return await self._create(data, item_id=item_id)

    async def add_to_location(self, location_id: str, data: bytes) -> PhotoRead:
        """Store a photo and attach it to a location.

        Args:
            location_id (str): The owning location id.
            data (bytes): Raw uploaded image bytes.

        Returns:
            PhotoRead: The created photo.

        Raises:
            NotFoundError: If the location does not exist.
            ValidationError: If the bytes are not a valid image.
        """
        if await self.locations.get(location_id) is None:
            raise NotFoundError("Local não encontrado.")
        return await self._create(data, location_id=location_id)

    async def delete(self, photo_id: str) -> None:
        """Delete a photo and its files.

        Args:
            photo_id (str): The photo id.

        Raises:
            NotFoundError: If the photo does not exist.
        """
        photo = await self.repository.get(photo_id)
        if photo is None:
            raise NotFoundError("Foto não encontrada.")
        self.storage.delete(photo.filename, photo.thumb_filename)
        await self.repository.delete(photo)
        await self.session.commit()

    async def _create(
        self, data: bytes, item_id: str | None = None, location_id: str | None = None
    ) -> PhotoRead:
        """Persist an uploaded image and its owner link.

        Args:
            data (bytes): Raw uploaded image bytes.
            item_id (str | None): Owning item id, if any.
            location_id (str | None): Owning location id, if any.

        Returns:
            PhotoRead: The created photo.

        Raises:
            ValidationError: If the bytes are not a valid image.
        """
        try:
            stored = self.storage.save_image(data)
        except ImageDecodeError as error:
            raise ValidationError("Arquivo de imagem inválido.") from error
        photo = Photo(
            item_id=item_id,
            location_id=location_id,
            filename=stored.filename,
            thumb_filename=stored.thumb_filename,
            content_type=stored.content_type,
            width=stored.width,
            height=stored.height,
        )
        await self.repository.add(photo)
        await self.session.commit()
        return to_photo_read(photo)
