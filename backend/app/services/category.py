"""Business logic for categories."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.errors import ConflictError, NotFoundError


class CategoryService:
    """Create, read, update, and delete item categories."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.repository = CategoryRepository(session)

    async def list(self) -> list[CategoryRead]:
        """Return all categories with their item counts, sorted by name.

        Returns:
            list[CategoryRead]: All categories.
        """
        categories = await self.repository.list_all()
        counts = await self.repository.counts_by_category()
        categories.sort(key=lambda category: category.name.lower())
        return [self._to_read(category, counts.get(category.id, 0)) for category in categories]

    async def create(self, data: CategoryCreate) -> CategoryRead:
        """Create a category.

        Args:
            data (CategoryCreate): The category to create.

        Returns:
            CategoryRead: The created category.

        Raises:
            ConflictError: If a category with the same name already exists.
        """
        if await self.repository.get_by_name(data.name) is not None:
            raise ConflictError("Já existe uma categoria com esse nome.")
        category = Category(name=data.name, color=data.color, icon=data.icon)
        await self.repository.add(category)
        await self.session.commit()
        return self._to_read(category, 0)

    async def update(self, category_id: str, data: CategoryUpdate) -> CategoryRead:
        """Update a category.

        Args:
            category_id (str): The category id.
            data (CategoryUpdate): Fields to change.

        Returns:
            CategoryRead: The updated category.

        Raises:
            NotFoundError: If the category does not exist.
            ConflictError: If renaming collides with another category.
        """
        category = await self._require(category_id)
        if data.name is not None and data.name != category.name:
            if await self.repository.get_by_name(data.name) is not None:
                raise ConflictError("Já existe uma categoria com esse nome.")
            category.name = data.name
        if data.color is not None:
            category.color = data.color
        if data.icon is not None:
            category.icon = data.icon
        await self.session.commit()
        counts = await self.repository.counts_by_category()
        return self._to_read(category, counts.get(category.id, 0))

    async def delete(self, category_id: str) -> None:
        """Delete a category (its item links are removed).

        Args:
            category_id (str): The category id.

        Raises:
            NotFoundError: If the category does not exist.
        """
        category = await self._require(category_id)
        await self.repository.delete(category)
        await self.session.commit()

    async def _require(self, category_id: str) -> Category:
        """Fetch a category or raise if missing.

        Args:
            category_id (str): The category id.

        Returns:
            Category: The found category.

        Raises:
            NotFoundError: If the category does not exist.
        """
        category = await self.repository.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        return category

    @staticmethod
    def _to_read(category: Category, item_count: int) -> CategoryRead:
        """Map a category to its read schema.

        Args:
            category (Category): The category to map.
            item_count (int): Number of items tagged with the category.

        Returns:
            CategoryRead: The populated read schema.
        """
        return CategoryRead(
            id=category.id,
            name=category.name,
            color=category.color,
            icon=category.icon,
            item_count=item_count,
        )
