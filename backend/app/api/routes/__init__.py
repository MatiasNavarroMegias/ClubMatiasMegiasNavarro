"""Rutas HTTP disponibles en la API."""

from app.api.routes.venues import router as venues_router

__all__ = ["venues_router"]
