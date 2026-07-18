"""Aggregate API router mounted under ``/api``."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    backup,
    categories,
    items,
    locations,
    meta,
    photos,
    printing,
    search,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(meta.router)
api_router.include_router(locations.router)
api_router.include_router(items.router)
api_router.include_router(categories.router)
api_router.include_router(photos.router)
api_router.include_router(search.router)
api_router.include_router(backup.router)
api_router.include_router(printing.router)
