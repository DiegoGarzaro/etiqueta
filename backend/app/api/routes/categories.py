"""Category endpoints."""

from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(session: SessionDep) -> list[CategoryRead]:
    """List all categories with item counts.

    Args:
        session (SessionDep): Database session.

    Returns:
        list[CategoryRead]: All categories.
    """
    return await CategoryService(session).list()


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, session: SessionDep) -> CategoryRead:
    """Create a category.

    Args:
        payload (CategoryCreate): The category to create.
        session (SessionDep): Database session.

    Returns:
        CategoryRead: The created category.
    """
    return await CategoryService(session).create(payload)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: str, payload: CategoryUpdate, session: SessionDep
) -> CategoryRead:
    """Update a category.

    Args:
        category_id (str): The category id.
        payload (CategoryUpdate): Fields to change.
        session (SessionDep): Database session.

    Returns:
        CategoryRead: The updated category.
    """
    return await CategoryService(session).update(category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, session: SessionDep) -> None:
    """Delete a category.

    Args:
        category_id (str): The category id.
        session (SessionDep): Database session.
    """
    await CategoryService(session).delete(category_id)
