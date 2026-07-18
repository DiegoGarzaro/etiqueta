"""Business logic for items."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.item import Item
from app.repositories.category import CategoryRepository
from app.repositories.item import ItemRepository
from app.repositories.location import LocationRepository
from app.schemas.category import CategoryRead
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate, LocationSummary
from app.services.errors import NotFoundError, ValidationError
from app.services.photo import to_photo_read
from app.services.text import normalize_text
from app.services.tree import LocationIndex


class ItemService:
    """Create, read, update, move, and delete catalogued items."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.repository = ItemRepository(session)
        self.location_repository = LocationRepository(session)
        self.category_repository = CategoryRepository(session)

    async def create(self, data: ItemCreate) -> ItemRead:
        """Create an item in a location with optional categories.

        Args:
            data (ItemCreate): The item to create.

        Returns:
            ItemRead: The created item with its location and categories.

        Raises:
            NotFoundError: If the target location does not exist.
            ValidationError: If any category id is unknown.
        """
        if await self.location_repository.get(data.location_id) is None:
            raise NotFoundError("Local não encontrado.")
        categories = await self._resolve_categories(data.category_ids)
        item = Item(
            name=data.name,
            description=data.description,
            quantity=data.quantity,
            notes=data.notes,
            location_id=data.location_id,
            search_text=normalize_text(data.name, data.description),
        )
        item.categories = categories
        item.photos = []
        await self.repository.add(item)
        await self.session.commit()
        index = await LocationIndex.create(self.session)
        return self._to_read(index, item)

    async def get(self, item_id: str) -> ItemRead:
        """Return a single item.

        Args:
            item_id (str): The item id.

        Returns:
            ItemRead: The item with its location and categories.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self._require(item_id)
        index = await LocationIndex.create(self.session)
        return self._to_read(index, item)

    async def list(
        self, location_id: str | None = None, category_id: str | None = None
    ) -> list[ItemRead]:
        """List items, optionally filtered by location subtree or category.

        Args:
            location_id (str | None): If set, include items in this subtree.
            category_id (str | None): If set, include only items with this category.

        Returns:
            list[ItemRead]: Matching items ordered by name.
        """
        index = await LocationIndex.create(self.session)
        items = await self.repository.list_all()
        if location_id is not None:
            allowed = index.subtree_ids(location_id)
            items = [item for item in items if item.location_id in allowed]
        if category_id is not None:
            items = [
                item for item in items if any(cat.id == category_id for cat in item.categories)
            ]
        items.sort(key=lambda item: item.name.lower())
        return [self._to_read(index, item) for item in items]

    async def update(self, item_id: str, data: ItemUpdate) -> ItemRead:
        """Update an item's fields, location, or categories.

        Args:
            item_id (str): The item id.
            data (ItemUpdate): Fields to change; ``category_ids`` replaces the full set.

        Returns:
            ItemRead: The updated item.

        Raises:
            NotFoundError: If the item or a new location does not exist.
            ValidationError: If any category id is unknown.
        """
        item = await self._require(item_id)
        if data.location_id is not None and data.location_id != item.location_id:
            if await self.location_repository.get(data.location_id) is None:
                raise NotFoundError("Local não encontrado.")
            item.location_id = data.location_id
        if data.name is not None:
            item.name = data.name
        if data.description is not None:
            item.description = data.description
        if data.quantity is not None:
            item.quantity = data.quantity
        if data.notes is not None:
            item.notes = data.notes
        if data.category_ids is not None:
            item.categories = await self._resolve_categories(data.category_ids)
        item.search_text = normalize_text(item.name, item.description)
        await self.session.commit()
        index = await LocationIndex.create(self.session)
        return self._to_read(index, item)

    async def delete(self, item_id: str) -> None:
        """Delete an item.

        Args:
            item_id (str): The item id.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self._require(item_id)
        await self.repository.delete(item)
        await self.session.commit()

    async def _require(self, item_id: str) -> Item:
        """Fetch an item or raise if missing.

        Args:
            item_id (str): The item id.

        Returns:
            Item: The found item.

        Raises:
            NotFoundError: If the item does not exist.
        """
        item = await self.repository.get(item_id)
        if item is None:
            raise NotFoundError("Item não encontrado.")
        return item

    async def _resolve_categories(self, category_ids: list[str]) -> list[Category]:
        """Resolve category ids to entities, requiring all to exist.

        Args:
            category_ids (list[str]): Requested category ids.

        Returns:
            list[Category]: The resolved categories.

        Raises:
            ValidationError: If any requested id has no matching category.
        """
        categories = await self.category_repository.get_by_ids(category_ids)
        if len(categories) != len(set(category_ids)):
            found = {category.id for category in categories}
            missing = [cid for cid in category_ids if cid not in found]
            raise ValidationError(f"Categorias não encontradas: {', '.join(missing)}")
        return categories

    def _to_read(self, index: LocationIndex, item: Item) -> ItemRead:
        """Map an item to its read schema.

        Args:
            index (LocationIndex): The current location index.
            item (Item): The item to map.

        Returns:
            ItemRead: The populated read schema.
        """
        location = index.by_id[item.location_id]
        return ItemRead(
            id=item.id,
            name=item.name,
            description=item.description,
            quantity=item.quantity,
            notes=item.notes,
            location=LocationSummary(
                id=location.id,
                name=location.name,
                code=location.code,
                full_code=index.full_code(location),
                path=index.path(location),
            ),
            categories=[
                CategoryRead(
                    id=category.id, name=category.name, color=category.color, icon=category.icon
                )
                for category in item.categories
            ],
            photos=[to_photo_read(photo) for photo in item.photos],
        )
