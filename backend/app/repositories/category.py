"""Data access for categories."""

from sqlalchemy import func, select

from app.models.associations import item_category
from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for :class:`~app.models.category.Category`."""

    model = Category

    async def get_by_ids(self, ids: list[str]) -> list[Category]:
        """Fetch categories matching the given ids.

        Args:
            ids (list[str]): Category ids to look up.

        Returns:
            list[Category]: Found categories (may be shorter than ``ids``).
        """
        if not ids:
            return []
        result = await self.session.execute(select(Category).where(Category.id.in_(ids)))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        """Fetch a category by its exact name.

        Args:
            name (str): The category name.

        Returns:
            Category | None: The category, or ``None`` if not found.
        """
        result = await self.session.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def counts_by_category(self) -> dict[str, int]:
        """Return the number of items tagged with each category.

        Returns:
            dict[str, int]: Mapping of ``category_id`` to item count.
        """
        result = await self.session.execute(
            select(item_category.c.category_id, func.count(item_category.c.item_id)).group_by(
                item_category.c.category_id
            )
        )
        return {category_id: count for category_id, count in result.all()}
