"""Rutas HTTP disponibles en la API."""

from app.api.routes.auth import router as auth_router
from app.api.routes.venues import router as venues_router

__all__ = [
    "auth_router",
    "venues_router",
]
