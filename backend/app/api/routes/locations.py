"""Location endpoints."""

from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.schemas.location import LocationCreate, LocationRead, LocationTreeNode, LocationUpdate
from app.services.location import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/tree", response_model=list[LocationTreeNode])
async def get_location_tree(session: SessionDep) -> list[LocationTreeNode]:
    """Return the full storage tree.

    Args:
        session (SessionDep): Database session.

    Returns:
        list[LocationTreeNode]: Nested locations, root cômodos first.
    """
    return await LocationService(session).list_tree()


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location(payload: LocationCreate, session: SessionDep) -> LocationRead:
    """Create a location.

    Args:
        payload (LocationCreate): The location to create.
        session (SessionDep): Database session.

    Returns:
        LocationRead: The created location.
    """
    return await LocationService(session).create(payload)


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(location_id: str, session: SessionDep) -> LocationRead:
    """Return a single location.

    Args:
        location_id (str): The location id.
        session (SessionDep): Database session.

    Returns:
        LocationRead: The location.
    """
    return await LocationService(session).get(location_id)


@router.patch("/{location_id}", response_model=LocationRead)
async def update_location(
    location_id: str, payload: LocationUpdate, session: SessionDep
) -> LocationRead:
    """Update a location.

    Args:
        location_id (str): The location id.
        payload (LocationUpdate): Fields to change.
        session (SessionDep): Database session.

    Returns:
        LocationRead: The updated location.
    """
    return await LocationService(session).update(location_id, payload)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: str, session: SessionDep, force: bool = False) -> None:
    """Delete a location.

    Args:
        location_id (str): The location id.
        session (SessionDep): Database session.
        force (bool): Delete children and items too when ``True``.
    """
    await LocationService(session).delete(location_id, force=force)
