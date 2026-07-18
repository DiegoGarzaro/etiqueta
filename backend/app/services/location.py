"""Business logic for locations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.repositories.location import LocationRepository
from app.schemas.location import LocationCreate, LocationRead, LocationTreeNode, LocationUpdate
from app.services.code import CodeService
from app.services.errors import ConflictError, NotFoundError, ValidationError
from app.services.photo import to_photo_read
from app.services.text import normalize_text
from app.services.tree import LocationIndex


class LocationService:
    """Create, read, move, and delete locations in the storage tree."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.repository = LocationRepository(session)

    async def create(self, data: LocationCreate) -> LocationRead:
        """Create a location and assign it a code segment.

        Args:
            data (LocationCreate): The location to create.

        Returns:
            LocationRead: The created location with derived fields.

        Raises:
            NotFoundError: If the given parent does not exist.
        """
        if data.parent_id is not None and await self.repository.get(data.parent_id) is None:
            raise NotFoundError("Local pai não encontrado.")
        code = await CodeService(self.repository).generate(data.parent_id, data.type)
        location = Location(
            name=data.name,
            type=data.type,
            parent_id=data.parent_id,
            code=code,
            notes=data.notes,
            search_text=normalize_text(data.name, code),
        )
        location.photos = []
        await self.repository.add(location)
        await self.session.commit()
        index = await LocationIndex.create(self.session)
        return self._to_read(index, location)

    async def get(self, location_id: str) -> LocationRead:
        """Return a single location.

        Args:
            location_id (str): The location id.

        Returns:
            LocationRead: The location with derived fields.

        Raises:
            NotFoundError: If the location does not exist.
        """
        location = await self._require(location_id)
        index = await LocationIndex.create(self.session)
        return self._to_read(index, location)

    async def list_tree(self) -> list[LocationTreeNode]:
        """Return the full location tree, root cômodos first.

        Returns:
            list[LocationTreeNode]: Nested tree nodes.
        """
        index = await LocationIndex.create(self.session)
        return [self._to_node(index, root) for root in index.children_of.get(None, [])]

    async def update(self, location_id: str, data: LocationUpdate) -> LocationRead:
        """Update a location's name, notes, or parent.

        Args:
            location_id (str): The location id.
            data (LocationUpdate): Fields to change.

        Returns:
            LocationRead: The updated location.

        Raises:
            NotFoundError: If the location or a new parent does not exist.
            ValidationError: If the move would create a cycle.
        """
        location = await self._require(location_id)
        if data.parent_id is not None and data.parent_id != location.parent_id:
            await self._guard_move(location, data.parent_id)
            location.parent_id = data.parent_id
        if data.name is not None:
            location.name = data.name
        if data.notes is not None:
            location.notes = data.notes
        location.search_text = normalize_text(location.name, location.code)
        await self.session.commit()
        index = await LocationIndex.create(self.session)
        return self._to_read(index, location)

    async def delete(self, location_id: str, force: bool = False) -> None:
        """Delete a location, optionally with its contents.

        Args:
            location_id (str): The location id.
            force (bool): If ``True``, delete children and items too.

        Raises:
            NotFoundError: If the location does not exist.
            ConflictError: If the location is not empty and ``force`` is ``False``.
        """
        location = await self._require(location_id)
        index = await LocationIndex.create(self.session)
        is_empty = not index.children_of.get(location.id) and index.total_count(location.id) == 0
        if not is_empty and not force:
            raise ConflictError(
                "Local não está vazio. Use force=true para excluir com o conteúdo."
            )
        await self.repository.delete(location)
        await self.session.commit()

    async def _require(self, location_id: str) -> Location:
        """Fetch a location or raise if missing.

        Args:
            location_id (str): The location id.

        Returns:
            Location: The found location.

        Raises:
            NotFoundError: If the location does not exist.
        """
        location = await self.repository.get(location_id)
        if location is None:
            raise NotFoundError("Local não encontrado.")
        return location

    async def _guard_move(self, location: Location, new_parent_id: str) -> None:
        """Validate that a move does not create a cycle.

        Args:
            location (Location): The location being moved.
            new_parent_id (str): The proposed new parent id.

        Raises:
            NotFoundError: If the new parent does not exist.
            ValidationError: If the new parent is the location or a descendant.
        """
        if new_parent_id == location.id:
            raise ValidationError("Um local não pode ser pai de si mesmo.")
        new_parent = await self.repository.get(new_parent_id)
        if new_parent is None:
            raise NotFoundError("Local pai não encontrado.")
        index = await LocationIndex.create(self.session)
        if location.id in {ancestor.id for ancestor in index.ancestors(new_parent)}:
            raise ValidationError("Não é possível mover um local para dentro de um descendente.")

    def _to_read(self, index: LocationIndex, location: Location) -> LocationRead:
        """Map a location to its read schema with derived fields.

        Args:
            index (LocationIndex): The current location index.
            location (Location): The location to map.

        Returns:
            LocationRead: The populated read schema.
        """
        return LocationRead(
            id=location.id,
            name=location.name,
            type=location.type,
            parent_id=location.parent_id,
            code=location.code,
            full_code=index.full_code(location),
            path=index.path(location),
            notes=location.notes,
            direct_item_count=index.direct_count(location.id),
            total_item_count=index.total_count(location.id),
            photos=[to_photo_read(photo) for photo in location.photos],
        )

    def _to_node(self, index: LocationIndex, location: Location) -> LocationTreeNode:
        """Recursively map a location to a nested tree node.

        Args:
            index (LocationIndex): The current location index.
            location (Location): The subtree root.

        Returns:
            LocationTreeNode: The node with nested children.
        """
        node = LocationTreeNode(**self._to_read(index, location).model_dump())
        node.children = [
            self._to_node(index, child) for child in index.children_of.get(location.id, [])
        ]
        return node
