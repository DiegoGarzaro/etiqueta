"""Search endpoint."""

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.search import SearchResults
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResults)
async def search_items(
    session: SessionDep,
    q: str = Query(..., min_length=1, description="Texto a buscar"),
    category_id: str | None = None,
) -> SearchResults:
    """Search items by name, description, or location text.

    Args:
        session (SessionDep): Database session.
        q (str): The query string.
        category_id (str | None): Optional category filter.

    Returns:
        SearchResults: Matching items with their locations.
    """
    return await SearchService(session).search(q, category_id=category_id)
