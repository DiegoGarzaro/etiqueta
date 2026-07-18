"""Filesystem storage for uploaded images, with thumbnail generation."""

import io
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

WEB_MAX_SIDE = 1600
THUMB_MAX_SIDE = 400


@dataclass
class StoredImage:
    """Metadata about a saved image pair.

    Attributes:
        filename (str): Filename of the web-sized image.
        thumb_filename (str): Filename of the thumbnail.
        width (int): Width of the web-sized image.
        height (int): Height of the web-sized image.
        content_type (str): MIME type of the stored image.
    """

    filename: str
    thumb_filename: str
    width: int
    height: int
    content_type: str


class ImageDecodeError(Exception):
    """Raised when uploaded bytes cannot be decoded as an image."""


class StorageService:
    """Saves and deletes images on the local filesystem."""

    def __init__(self, media_dir: str) -> None:
        """Initialize the service and ensure the media directory exists.

        Args:
            media_dir (str): Directory where images are written.
        """
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, data: bytes) -> StoredImage:
        """Store a web-sized image and a thumbnail from raw upload bytes.

        The image is EXIF-rotated, converted to RGB, downscaled, and written
        as two JPEGs (web + thumbnail).

        Args:
            data (bytes): Raw uploaded image bytes.

        Returns:
            StoredImage: Filenames and dimensions of the stored images.

        Raises:
            ImageDecodeError: If the bytes are not a decodable image.
        """
        try:
            with Image.open(io.BytesIO(data)) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
        except (UnidentifiedImageError, OSError) as error:
            raise ImageDecodeError(str(error)) from error

        name = uuid.uuid4().hex
        filename = f"{name}.jpg"
        thumb_filename = f"{name}_thumb.jpg"

        web = self._fit(image, WEB_MAX_SIDE)
        thumb = self._fit(image, THUMB_MAX_SIDE)
        web.save(self.media_dir / filename, "JPEG", quality=85, optimize=True)
        thumb.save(self.media_dir / thumb_filename, "JPEG", quality=80, optimize=True)

        return StoredImage(filename, thumb_filename, web.width, web.height, "image/jpeg")

    def delete(self, *filenames: str) -> None:
        """Delete stored files if they exist.

        Args:
            *filenames (str): Filenames to remove from the media directory.
        """
        for filename in filenames:
            path = self.media_dir / filename
            if path.exists():
                path.unlink()

    @staticmethod
    def _fit(image: Image.Image, max_side: int) -> Image.Image:
        """Return a copy scaled to fit within a square bound.

        Args:
            image (Image.Image): Source image.
            max_side (int): Maximum width/height in pixels.

        Returns:
            Image.Image: The resized copy.
        """
        copy = image.copy()
        copy.thumbnail((max_side, max_side))
        return copy
