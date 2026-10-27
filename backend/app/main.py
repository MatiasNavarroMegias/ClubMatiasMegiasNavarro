from fastapi import FastAPI

from app.api.routes import (
    auth_router,
    reservations_router,
    sports_spaces_router,
    users_router,
    venues_router,
)

# Esta instancia representa la aplicacion web principal.
# FastAPI utiliza esta configuracion para registrar las rutas
# y generar automaticamente la documentacion OpenAPI.
app = FastAPI(
    title="ClubMatiasMegiasNavarro API",
    description="API REST para la gestion de espacios deportivos.",
    version="0.1.0",
)


# Registra los endpoints disponibles dentro de la aplicacion.
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(venues_router)
app.include_router(sports_spaces_router)
app.include_router(reservations_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """
    Comprueba que la API se encuentra disponible.

    Este endpoint no consulta la base de datos. Su objetivo es
    verificar que el servidor FastAPI puede recibir solicitudes
    HTTP y devolver una respuesta JSON.

    Returns:
        Un diccionario con el estado y el nombre del servicio.
    """
    return {
        "status": "ok",
        "service": "ClubMatiasMegiasNavarro API",
    }
