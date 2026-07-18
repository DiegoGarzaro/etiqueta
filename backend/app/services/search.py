"""Business logic for global search."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.item import ItemRepository
from app.schemas.search import SearchResults
from app.services.item import ItemService
from app.services.text import normalize_text
from app.services.tree import LocationIndex


class SearchService:
    """Search items by name, description, or location text."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.repository = ItemRepository(session)
        self.item_service = ItemService(session)

    async def search(self, query: str, category_id: str | None = None) -> SearchResults:
        """Run an accent-insensitive search over items.

        Args:
            query (str): The user's query string.
            category_id (str | None): If set, restrict results to this category.

        Returns:
            SearchResults: The query, total count, and matching items.
        """
        normalized = normalize_text(query)
        if not normalized:
            return SearchResults(query=query, total=0, items=[])
        items = await self.repository.search(normalized)
        if category_id is not None:
            items = [
                item for item in items if any(cat.id == category_id for cat in item.categories)
            ]
        index = await LocationIndex.create(self.session)
        reads = [self.item_service._to_read(index, item) for item in items]
        return SearchResults(query=query, total=len(reads), items=reads)
