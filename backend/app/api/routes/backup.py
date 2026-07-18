"""Backup endpoints: export (JSON/CSV) and import (JSON restore)."""

from fastapi import APIRouter, Response

from app.api.deps import SessionDep
from app.schemas.backup import BackupData, ImportResult
from app.services.backup import BackupService

router = APIRouter(tags=["backup"])


@router.get("/export", response_model=BackupData)
async def export_inventory(session: SessionDep) -> BackupData:
    """Export the entire inventory as a JSON snapshot.

    Args:
        session (SessionDep): Database session.

    Returns:
        BackupData: The full inventory.
    """
    return await BackupService(session).export()


@router.get("/export.csv")
async def export_items_csv(session: SessionDep) -> Response:
    """Export items as a downloadable CSV file.

    Args:
        session (SessionDep): Database session.

    Returns:
        Response: A ``text/csv`` attachment.
    """
    csv_text = await BackupService(session).export_items_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="inventario.csv"'},
    )


@router.post("/import", response_model=ImportResult)
async def import_inventory(payload: BackupData, session: SessionDep) -> ImportResult:
    """Replace the entire inventory with an uploaded JSON backup.

    Args:
        payload (BackupData): The backup snapshot to restore.
        session (SessionDep): Database session.

    Returns:
        ImportResult: Counts of restored records.
    """
    return await BackupService(session).import_data(payload)
