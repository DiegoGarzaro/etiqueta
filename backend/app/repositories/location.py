"""Data access for locations."""

from sqlalchemy import select

from app.models.location import Location, LocationType
from app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    """Repository for :class:`~app.models.location.Location`."""

    model = Location

    async def get_children(self, parent_id: str | None) -> list[Location]:
        """Return the direct children of a location.

        Args:
            parent_id (str | None): Parent id, or ``None`` for root cômodos.

        Returns:
            list[Location]: Direct child locations.
        """
        result = await self.session.execute(
            select(Location).where(Location.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def count_siblings_of_type(
        self, parent_id: str | None, type_: LocationType
    ) -> int:
        """Count existing siblings of a given type under a parent.

        Args:
            parent_id (str | None): Parent id, or ``None`` for root cômodos.
            type_ (LocationType): The location type to count.

        Returns:
            int: Number of matching siblings.
        """
        result = await self.session.execute(
            select(Location).where(
                Location.parent_id == parent_id, Location.type == type_
            )
        )
        return len(result.scalars().all())
