"""Data access for items."""

from sqlalchemy import func, or_, select

from app.models.item import Item
from app.models.location import Location
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """Repository for :class:`~app.models.item.Item`."""

    model = Item

    async def counts_by_location(self) -> dict[str, int]:
        """Return the number of items stored directly in each location.

        Returns:
            dict[str, int]: Mapping of ``location_id`` to direct item count.
        """
        result = await self.session.execute(
            select(Item.location_id, func.count(Item.id)).group_by(Item.location_id)
        )
        return {location_id: count for location_id, count in result.all()}

    async def list_by_location(self, location_id: str) -> list[Item]:
        """Return items stored directly in a location.

        Args:
            location_id (str): The owning location id.

        Returns:
            list[Item]: Items in that location (categories eager-loaded).
        """
        result = await self.session.execute(
            select(Item).where(Item.location_id == location_id).order_by(Item.name)
        )
        return list(result.scalars().all())

    async def search(self, normalized_query: str) -> list[Item]:
        """Search items by normalized item text or their location text.

        Args:
            normalized_query (str): Accent-insensitive, lowercased query.

        Returns:
            list[Item]: Matching items ordered by name.
        """
        pattern = f"%{normalized_query}%"
        result = await self.session.execute(
            select(Item)
            .join(Location, Item.location_id == Location.id)
            .where(
                or_(
                    Item.search_text.like(pattern),
                    Location.search_text.like(pattern),
                )
            )
            .order_by(Item.name)
        )
        return list(result.scalars().unique().all())
