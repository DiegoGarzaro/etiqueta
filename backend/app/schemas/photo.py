"""Pydantic schemas for photos."""

from pydantic import BaseModel


class PhotoRead(BaseModel):
    """A photo as returned by the API.

    Attributes:
        id (str): Photo id.
        url (str): URL of the web-sized image.
        thumb_url (str): URL of the thumbnail.
        content_type (str): MIME type of the image.
        width (int): Width of the web-sized image in pixels.
        height (int): Height of the web-sized image in pixels.
    """

    id: str
    url: str
    thumb_url: str
    content_type: str
    width: int
    height: int
