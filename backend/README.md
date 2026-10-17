# Backend

API REST de ClubMatiasMegiasNavarro desarrollada con FastAPI y PostgreSQL.

## Requisitos

- Python 3.14
- PostgreSQL 18

## Crear el entorno virtual

Desde la carpeta `backend`:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Instalar las dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Variables de entorno

Copiar `.env.example` como `.env`:

```powershell
Copy-Item .env.example .env
```

Luego deben completarse las variables locales dentro del archivo `.env`.

El archivo `.env` contiene configuración privada y no debe registrarse en Git.

## Verificar las dependencias

```powershell
python -m pip check
```

## Ejecutar las pruebas

```powershell
python -m pytest
```

## Analizar y comprobar el formato

```powershell
ruff check .
ruff format --check .
```

## Ejecutar la API en desarrollo

Con el entorno virtual activo y desde la carpeta `backend`:

```powershell
python -m uvicorn app.main:app --reload
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

La opcion `--reload` reinicia automaticamente el servidor cuando se modifica el codigo. Esta opcion se utiliza solamente durante el desarrollo.

## Verificar el estado de la API

El endpoint de salud permite comprobar que el servidor se encuentra disponible:

```text
GET http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "ClubMatiasMegiasNavarro API"
}
```

Este endpoint no consulta PostgreSQL. Su objetivo es comprobar solamente que FastAPI puede recibir solicitudes y devolver respuestas HTTP.

## Documentacion de la API

FastAPI genera automaticamente documentacion interactiva mediante OpenAPI.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Detener la API

En la terminal donde se esta ejecutando Uvicorn:

```text
Ctrl + C
```