"""In-memory index over the location tree for computing derived data.

Loading every location once and assembling the tree in Python keeps the derived
values (full code, path, subtree counts) simple and avoids async lazy-loading
pitfalls. This is appropriate for a single-household inventory.
"""

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location, LocationType
from app.repositories.item import ItemRepository
from app.repositories.location import LocationRepository
from app.schemas.location import PathSegment


class LocationIndex:
    """Snapshot of all locations with helpers for derived values.

    Attributes:
        by_id (dict[str, Location]): Locations keyed by id.
        children_of (dict[str | None, list[Location]]): Children keyed by parent id.
        direct_counts (dict[str, int]): Direct item count per location id.
    """

    def __init__(self, locations: list[Location], direct_counts: dict[str, int]) -> None:
        """Build the index from loaded locations and item counts.

        Args:
            locations (list[Location]): All locations in the database.
            direct_counts (dict[str, int]): Direct item counts keyed by location id.
        """
        self.by_id: dict[str, Location] = {loc.id: loc for loc in locations}
        self.children_of: dict[str | None, list[Location]] = defaultdict(list)
        for loc in locations:
            self.children_of[loc.parent_id].append(loc)
        for siblings in self.children_of.values():
            siblings.sort(key=lambda location: (location.type.value, location.code, location.name))
        self.direct_counts = direct_counts
        self._total_cache: dict[str, int] = {}

    @classmethod
    async def create(cls, session: AsyncSession) -> "LocationIndex":
        """Load all locations and item counts and build an index.

        Args:
            session (AsyncSession): The active database session.

        Returns:
            LocationIndex: A ready-to-query index.
        """
        locations = await LocationRepository(session).list_all()
        counts = await ItemRepository(session).counts_by_location()
        return cls(locations, counts)

    def ancestors(self, location: Location) -> list[Location]:
        """Return the chain from the root cômodo down to ``location``.

        Args:
            location (Location): The location whose ancestry to resolve.

        Returns:
            list[Location]: Locations ordered root-first, ending with ``location``.
        """
        chain: list[Location] = []
        seen: set[str] = set()
        current: Location | None = location
        while current is not None and current.id not in seen:
            seen.add(current.id)
            chain.append(current)
            current = self.by_id.get(current.parent_id) if current.parent_id else None
        chain.reverse()
        return chain

    def path(self, location: Location) -> list[PathSegment]:
        """Return the location's path as serializable segments.

        Args:
            location (Location): The target location.

        Returns:
            list[PathSegment]: Root-first path including the location itself.
        """
        return [
            PathSegment(id=node.id, name=node.name, code=node.code)
            for node in self.ancestors(location)
        ]

    def full_code(self, location: Location) -> str:
        """Return the tag code joining non-room ancestor codes.

        Example: an armário/gaveta chain yields ``"ARM-A · GAV-02"``.

        Args:
            location (Location): The target location.

        Returns:
            str: The joined code, or the location's own code if it is a cômodo.
        """
        codes = [
            node.code
            for node in self.ancestors(location)
            if node.type != LocationType.COMODO
        ]
        return " · ".join(codes) if codes else location.code

    def direct_count(self, location_id: str) -> int:
        """Return items stored directly in a location.

        Args:
            location_id (str): The location id.

        Returns:
            int: Direct item count.
        """
        return self.direct_counts.get(location_id, 0)

    def total_count(self, location_id: str) -> int:
        """Return items in a location and all of its descendants.

        Args:
            location_id (str): The location id.

        Returns:
            int: Total item count in the subtree.
        """
        if location_id in self._total_cache:
            return self._total_cache[location_id]
        total = self.direct_counts.get(location_id, 0)
        for child in self.children_of.get(location_id, []):
            total += self.total_count(child.id)
        self._total_cache[location_id] = total
        return total

    def subtree_ids(self, location_id: str) -> set[str]:
        """Return the ids of a location and all its descendants.

        Args:
            location_id (str): The subtree root id.

        Returns:
            set[str]: Ids in the subtree, including the root.
        """
        ids = {location_id}
        for child in self.children_of.get(location_id, []):
            ids |= self.subtree_ids(child.id)
        return ids
