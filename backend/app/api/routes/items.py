"""Item endpoints."""

from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate
from app.services.item import ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemRead])
async def list_items(
    session: SessionDep, location_id: str | None = None, category_id: str | None = None
) -> list[ItemRead]:
    """List items, optionally filtered by location subtree or category.

    Args:
        session (SessionDep): Database session.
        location_id (str | None): Restrict to this location's subtree.
        category_id (str | None): Restrict to items with this category.

    Returns:
        list[ItemRead]: Matching items.
    """
    return await ItemService(session).list(location_id=location_id, category_id=category_id)


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, session: SessionDep) -> ItemRead:
    """Create an item.

    Args:
        payload (ItemCreate): The item to create.
        session (SessionDep): Database session.

    Returns:
        ItemRead: The created item.
    """
    return await ItemService(session).create(payload)


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: str, session: SessionDep) -> ItemRead:
    """Return a single item.

    Args:
        item_id (str): The item id.
        session (SessionDep): Database session.

    Returns:
        ItemRead: The item.
    """
    return await ItemService(session).get(item_id)


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(item_id: str, payload: ItemUpdate, session: SessionDep) -> ItemRead:
    """Update an item.

    Args:
        item_id (str): The item id.
        payload (ItemUpdate): Fields to change.
        session (SessionDep): Database session.

    Returns:
        ItemRead: The updated item.
    """
    return await ItemService(session).update(item_id, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str, session: SessionDep) -> None:
    """Delete an item.

    Args:
        item_id (str): The item id.
        session (SessionDep): Database session.
    """
    await ItemService(session).delete(item_id)
