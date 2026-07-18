"""Photo upload and delete endpoints."""

from fastapi import APIRouter, UploadFile, status

from app.api.deps import SessionDep
from app.schemas.photo import PhotoRead
from app.services.photo import PhotoService

router = APIRouter(tags=["photos"])


@router.post(
    "/items/{item_id}/photos", response_model=PhotoRead, status_code=status.HTTP_201_CREATED
)
async def upload_item_photo(item_id: str, file: UploadFile, session: SessionDep) -> PhotoRead:
    """Attach an uploaded photo to an item.

    Args:
        item_id (str): The owning item id.
        file (UploadFile): The uploaded image.
        session (SessionDep): Database session.

    Returns:
        PhotoRead: The stored photo.
    """
    data = await file.read()
    return await PhotoService(session).add_to_item(item_id, data)


@router.post(
    "/locations/{location_id}/photos",
    response_model=PhotoRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_location_photo(
    location_id: str, file: UploadFile, session: SessionDep
) -> PhotoRead:
    """Attach an uploaded photo to a location.

    Args:
        location_id (str): The owning location id.
        file (UploadFile): The uploaded image.
        session (SessionDep): Database session.

    Returns:
        PhotoRead: The stored photo.
    """
    data = await file.read()
    return await PhotoService(session).add_to_location(location_id, data)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: str, session: SessionDep) -> None:
    """Delete a photo and its files.

    Args:
        photo_id (str): The photo id.
        session (SessionDep): Database session.
    """
    await PhotoService(session).delete(photo_id)
