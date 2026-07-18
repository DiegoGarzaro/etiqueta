"""Full-inventory export (JSON/CSV) and import (JSON restore)."""

import csv
import io
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.item import Item
from app.models.location import Location
from app.models.photo import Photo
from app.repositories.category import CategoryRepository
from app.repositories.item import ItemRepository
from app.repositories.location import LocationRepository
from app.repositories.photo import PhotoRepository
from app.schemas.backup import (
    BackupCategory,
    BackupData,
    BackupItem,
    BackupLocation,
    BackupPhoto,
    ImportResult,
)
from app.services.text import normalize_text
from app.services.tree import LocationIndex


class BackupService:
    """Exports the whole inventory and restores it from a backup."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session (AsyncSession): The active database session.
        """
        self.session = session
        self.locations = LocationRepository(session)
        self.categories = CategoryRepository(session)
        self.items = ItemRepository(session)
        self.photos = PhotoRepository(session)

    async def export(self) -> BackupData:
        """Gather the entire inventory into a backup snapshot.

        Returns:
            BackupData: All categories, locations, items, and photo metadata.
        """
        categories = await self.categories.list_all()
        locations = await self.locations.list_all()
        items = await self.items.list_all()
        photos = await self.photos.list_all()
        return BackupData(
            exported_at=datetime.now(UTC).isoformat(),
            categories=[
                BackupCategory(id=c.id, name=c.name, color=c.color, icon=c.icon)
                for c in categories
            ],
            locations=[
                BackupLocation(
                    id=loc.id,
                    name=loc.name,
                    type=loc.type,
                    parent_id=loc.parent_id,
                    code=loc.code,
                    notes=loc.notes,
                )
                for loc in locations
            ],
            items=[
                BackupItem(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    quantity=item.quantity,
                    notes=item.notes,
                    location_id=item.location_id,
                    category_ids=[category.id for category in item.categories],
                )
                for item in items
            ],
            photos=[
                BackupPhoto(
                    id=photo.id,
                    item_id=photo.item_id,
                    location_id=photo.location_id,
                    filename=photo.filename,
                    thumb_filename=photo.thumb_filename,
                    content_type=photo.content_type,
                    width=photo.width,
                    height=photo.height,
                )
                for photo in photos
            ],
        )

    async def export_items_csv(self) -> str:
        """Export items as a flat CSV with their location and categories.

        Returns:
            str: CSV text with a header row.
        """
        index = await LocationIndex.create(self.session)
        items = await self.items.list_all()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["Item", "Quantidade", "Código do local", "Caminho", "Categorias", "Descrição"]
        )
        for item in sorted(items, key=lambda entry: entry.name.lower()):
            location = index.by_id.get(item.location_id)
            full_code = index.full_code(location) if location else ""
            path = (
                " › ".join(segment.name for segment in index.path(location)) if location else ""
            )
            categories = ", ".join(category.name for category in item.categories)
            writer.writerow(
                [item.name, item.quantity, full_code, path, categories, item.description or ""]
            )
        return buffer.getvalue()

    async def import_data(self, data: BackupData) -> ImportResult:
        """Replace the entire inventory with the contents of a backup.

        Existing data is deleted first, then records are inserted with their
        original ids so photo file references stay valid.

        Args:
            data (BackupData): The backup snapshot to restore.

        Returns:
            ImportResult: Counts of restored records.
        """
        await self._wipe()

        for category in data.categories:
            self.session.add(
                Category(
                    id=category.id, name=category.name, color=category.color, icon=category.icon
                )
            )

        for location in self._parents_first(data.locations):
            self.session.add(
                Location(
                    id=location.id,
                    name=location.name,
                    type=location.type,
                    parent_id=location.parent_id,
                    code=location.code,
                    notes=location.notes,
                    search_text=normalize_text(location.name, location.code),
                )
            )
        await self.session.flush()

        categories_by_id = {category.id: category for category in await self.categories.list_all()}
        for item in data.items:
            entity = Item(
                id=item.id,
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                notes=item.notes,
                location_id=item.location_id,
                search_text=normalize_text(item.name, item.description),
            )
            entity.categories = [
                categories_by_id[cid] for cid in item.category_ids if cid in categories_by_id
            ]
            entity.photos = []
            self.session.add(entity)
        await self.session.flush()

        for photo in data.photos:
            self.session.add(
                Photo(
                    id=photo.id,
                    item_id=photo.item_id,
                    location_id=photo.location_id,
                    filename=photo.filename,
                    thumb_filename=photo.thumb_filename,
                    content_type=photo.content_type,
                    width=photo.width,
                    height=photo.height,
                )
            )

        await self.session.commit()
        return ImportResult(
            categories=len(data.categories),
            locations=len(data.locations),
            items=len(data.items),
            photos=len(data.photos),
        )

    async def _wipe(self) -> None:
        """Delete all inventory rows (photos, items, categories, locations)."""
        for model in (Photo, Item, Category, Location):
            await self.session.execute(delete(model))
        await self.session.flush()

    @staticmethod
    def _parents_first(locations: list[BackupLocation]) -> list[BackupLocation]:
        """Order locations so every parent precedes its children.

        Args:
            locations (list[BackupLocation]): Locations in any order.

        Returns:
            list[BackupLocation]: Locations ordered for safe FK insertion.
        """
        remaining = list(locations)
        ordered: list[BackupLocation] = []
        inserted: set[str] = set()
        while remaining:
            progressed = False
            still_waiting: list[BackupLocation] = []
            for location in remaining:
                if location.parent_id is None or location.parent_id in inserted:
                    ordered.append(location)
                    inserted.add(location.id)
                    progressed = True
                else:
                    still_waiting.append(location)
            remaining = still_waiting
            if not progressed:
                # Orphaned parents (bad data): append the rest as-is.
                ordered.extend(remaining)
                break
        return ordered
