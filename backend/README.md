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