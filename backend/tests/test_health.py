from fastapi.testclient import TestClient

from app.main import app

# TestClient permite probar la API sin iniciar un servidor Uvicorn real.
# Las solicitudes se ejecutan directamente sobre la aplicacion FastAPI.
client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    """
    Verifica que el endpoint de salud responda correctamente.

    La prueba comprueba el codigo HTTP y el contenido JSON.
    Si una modificacion futura rompe el endpoint, Pytest informara
    exactamente que resultado no coincide con lo esperado.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ClubMatiasMegiasNavarro API",
    }
