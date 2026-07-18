"""Generic async repository base class."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[ModelT: Base]:
    """Async CRUD data-access helper for a single model.

    Attributes:
        model (type[ModelT]): The ORM model this repository manages.
        session (AsyncSession): The active database session.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session

    async def get(self, obj_id: str) -> ModelT | None:
        """Fetch a row by primary key.

        Args:
            obj_id (str): The primary key value.

        Returns:
            ModelT | None: The row, or ``None`` if not found.
        """
        return await self.session.get(self.model, obj_id)

    async def list_all(self) -> list[ModelT]:
        """Return all rows for the model.

        Returns:
            list[ModelT]: Every row in the table.
        """
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def add(self, obj: ModelT) -> ModelT:
        """Persist a new object and flush to assign defaults.

        Args:
            obj (ModelT): The object to persist.

        Returns:
            ModelT: The same object, flushed to the session.
        """
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Delete an object from the session.

        Args:
            obj (ModelT): The object to delete.
        """
        await self.session.delete(obj)
