"""Populate the database with a small, realistic sample inventory.

Run from the ``backend`` directory:

    uv run python -m scripts.seed
"""

import asyncio

from app.core.database import async_session_factory, init_db
from app.models.location import LocationType
from app.repositories.location import LocationRepository
from app.schemas.category import CategoryCreate
from app.schemas.item import ItemCreate
from app.schemas.location import LocationCreate
from app.services.category import CategoryService
from app.services.item import ItemService
from app.services.location import LocationService


async def seed() -> None:
    """Create example locations, categories, and items if the database is empty."""
    await init_db()
    async with async_session_factory() as session:
        if await LocationRepository(session).list_all():
            print("Database already has data — nothing to seed.")
            return

        locations = LocationService(session)
        categories = CategoryService(session)
        items = ItemService(session)

        office = await locations.create(
            LocationCreate(name="Escritório", type=LocationType.COMODO)
        )
        wardrobe = await locations.create(
            LocationCreate(name="Armário A", type=LocationType.ARMARIO, parent_id=office.id)
        )
        drawer = await locations.create(
            LocationCreate(name="Gaveta 2", type=LocationType.GAVETA, parent_id=wardrobe.id)
        )

        electronics = await categories.create(
            CategoryCreate(name="Eletrônicos", color="#2F6B4F")
        )
        stationery = await categories.create(
            CategoryCreate(name="Papelaria", color="#7A5AA0")
        )

        await items.create(
            ItemCreate(
                name="Carregador USB-C",
                quantity=2,
                location_id=drawer.id,
                category_ids=[electronics.id],
            )
        )
        await items.create(
            ItemCreate(
                name="Câmera fotográfica",
                location_id=drawer.id,
                category_ids=[electronics.id],
            )
        )
        await items.create(
            ItemCreate(
                name="Bloco de notas",
                quantity=5,
                location_id=drawer.id,
                category_ids=[stationery.id],
            )
        )

    print("Seed complete: 3 locations, 2 categories, 3 items.")


if __name__ == "__main__":
    asyncio.run(seed())
