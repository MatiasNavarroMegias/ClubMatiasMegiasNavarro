from fastapi import FastAPI

from app.api.routes import venues_router

# Esta instancia representa la aplicacion web principal.
# FastAPI utiliza esta configuracion para registrar las rutas
# y generar automaticamente la documentacion OpenAPI.
app = FastAPI(
    title="ClubMatiasMegiasNavarro API",
    description="API REST para la gestion de espacios deportivos.",
    version="0.1.0",
)


# Importar un router no registra automaticamente sus endpoints.
# include_router conecta las rutas de sedes con la aplicacion principal.
app.include_router(venues_router)


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
