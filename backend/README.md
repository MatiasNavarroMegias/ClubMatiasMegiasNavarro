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

## Configuracion mediante variables de entorno

El backend utiliza `pydantic-settings` para leer y validar su configuracion.

Durante el desarrollo local, los valores se obtienen desde:

```text
backend/.env
```

El archivo `.env` contiene informacion especifica del entorno local y puede incluir datos privados, como la contrasena de PostgreSQL. Por este motivo, no debe registrarse en Git.

## Crear el archivo `.env`

Desde la carpeta `backend`:

```powershell
Copy-Item .env.example .env
```

Luego se deben completar los valores locales dentro de `.env`.

Ejemplo:

```env
APP_NAME=ClubMatiasMegiasNavarro API
APP_ENV=development
APP_DEBUG=true
DATABASE_URL=postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/club_matias_megias_navarro
```

El texto `TU_CONTRASENA` debe reemplazarse solamente dentro del archivo `.env`.

La contrasena real no debe escribirse en:

- `.env.example`
- Archivos Python
- README
- Commits
- Pull Requests
- Capturas publicas

## Variables disponibles

### `APP_NAME`

Define el nombre utilizado para identificar la API.

```env
APP_NAME=ClubMatiasMegiasNavarro API
```

### `APP_ENV`

Define el entorno actual de ejecucion.

Valores permitidos:

```text
development
testing
production
```

### `APP_DEBUG`

Indica si la aplicacion utiliza configuraciones de depuracion.

```env
APP_DEBUG=true
```

`pydantic-settings` convierte el texto `true` en el valor booleano `True`.

### `DATABASE_URL`

Define la direccion que utilizara SQLAlchemy para conectarse con PostgreSQL.

```env
DATABASE_URL=postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/club_matias_megias_navarro
```

## Verificar la configuracion

Con el entorno virtual activo y desde la carpeta `backend`:

```powershell
python -c "from app.core.config import get_settings; settings = get_settings(); print(settings.app_name, settings.app_env, settings.app_debug)"
```

Resultado esperado:

```text
ClubMatiasMegiasNavarro API development True
```

La URL de la base de datos no se imprime para evitar mostrar accidentalmente la contrasena.

## Archivo `.env.example`

El archivo `.env.example` se registra en Git porque documenta las variables necesarias sin incluir valores privados.

El archivo `.env` se excluye mediante `.gitignore` porque contiene la configuracion real del entorno local.

## Base de datos local

El backend utiliza PostgreSQL como base de datos relacional y SQLAlchemy para administrar las conexiones desde Python.

### Verificar el servicio de PostgreSQL

En Windows:

```powershell
Get-Service postgresql-x64-18
```

El servicio debe mostrar el estado:

```text
Running
```

Si el servicio esta detenido, debe iniciarse desde una terminal con permisos de administrador:

```powershell
Start-Service postgresql-x64-18
```

### Crear la base de datos

Ingresar a PostgreSQL:

```powershell
psql -h localhost -p 5432 -U postgres -d postgres
```

Dentro de `psql`, crear la base:

```sql
CREATE DATABASE club_matias_megias_navarro;
```

Luego conectarse:

```text
\c club_matias_megias_navarro
```

Verificar la base y el usuario actuales:

```sql
SELECT current_database(), current_user;
```

Para salir de PostgreSQL:

```text
\q
```

### Configurar la conexion

La conexion se define localmente dentro de `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/club_matias_megias_navarro
```

El texto `TU_CONTRASENA` debe reemplazarse solamente dentro de `.env`.

Si la contrasena contiene caracteres especiales, debe codificarse para que pueda formar parte de una URL.

El archivo `.env` no debe registrarse en Git.

### Verificar la conexion desde SQLAlchemy

Con el entorno virtual activo y desde la carpeta `backend`:

```powershell
python -c "from sqlalchemy import text; from app.core.database import engine; connection = engine.connect(); print(connection.execute(text('SELECT current_database()')).scalar_one()); connection.close()"
```

Resultado esperado:

```text
club_matias_megias_navarro
```

Verificar el usuario conectado:

```powershell
python -c "from sqlalchemy import text; from app.core.database import engine; connection = engine.connect(); print(connection.execute(text('SELECT current_user')).scalar_one()); connection.close()"
```

Resultado esperado:

```text
postgres
```

Estas verificaciones solamente consultan informacion de la conexion. No crean tablas ni modifican datos.

## Estructura de conexion

El archivo `app/core/database.py` contiene:

- El motor de SQLAlchemy.
- La fabrica de sesiones.
- La clase base para los futuros modelos.
- La dependencia que entrega y cierra sesiones.

Las tablas no se crean manualmente desde este archivo. La estructura de PostgreSQL se administrara mediante modelos de SQLAlchemy y migraciones de Alembic.

## Migraciones de base de datos

El backend utiliza Alembic para versionar los cambios estructurales realizados sobre PostgreSQL.

Una migracion permite registrar operaciones como:

- Crear una tabla.
- Agregar o eliminar una columna.
- Modificar un tipo de dato.
- Crear indices.
- Agregar restricciones.
- Crear claves foraneas.

Los cambios de estructura no deben realizarse manualmente en PostgreSQL. Deben representarse mediante modelos de SQLAlchemy y migraciones de Alembic.

## Estructura de Alembic

```text
backend/
├── alembic.ini
└── migrations/
    ├── env.py
    ├── README
    ├── script.py.mako
    └── versions/
```

### `alembic.ini`

Contiene la configuracion general de Alembic.

La URL real de PostgreSQL no se guarda en este archivo. Alembic obtiene `DATABASE_URL` desde la configuracion central del backend.

### `migrations/env.py`

Conecta Alembic con:

- La configuracion basada en variables de entorno.
- PostgreSQL.
- El motor de SQLAlchemy.
- Los metadatos de los futuros modelos.

### `migrations/script.py.mako`

Es la plantilla utilizada para generar nuevos archivos de migracion.

### `migrations/versions`

Contiene las migraciones versionadas del proyecto.

La carpeta puede permanecer vacia hasta crear la primera migracion.

## Verificar la configuracion de Alembic

Con el entorno virtual activo y desde la carpeta `backend`:

```powershell
python -m alembic current
```

El comando muestra la revision aplicada actualmente en PostgreSQL.

Si todavia no existen migraciones, el comando puede no mostrar un identificador de revision.

## Consultar la revision mas reciente

```powershell
python -m alembic heads
```

El comando muestra la ultima revision disponible dentro del proyecto.

## Consultar el historial

```powershell
python -m alembic history
```

El comando muestra todas las migraciones en orden.

## Crear una migracion automatica

Cuando existan modelos de SQLAlchemy:

```powershell
python -m alembic revision --autogenerate -m "descripcion del cambio"
```

Antes de aplicar una migracion generada automaticamente, se debe revisar su contenido.

Alembic detecta diferencias entre:

- Los modelos definidos mediante SQLAlchemy.
- La estructura actual de PostgreSQL.

## Aplicar migraciones pendientes

```powershell
python -m alembic upgrade head
```

`head` representa la revision mas reciente disponible.

## Revertir la ultima migracion

```powershell
python -m alembic downgrade -1
```

Este comando revierte solamente la ultima revision aplicada.

Una migracion no debe revertirse sin revisar primero las operaciones definidas en su funcion `downgrade`.

## Flujo recomendado

```text
Modificar o crear un modelo SQLAlchemy
→ Generar una migracion automatica
→ Revisar las funciones upgrade y downgrade
→ Ejecutar las pruebas
→ Aplicar la migracion en PostgreSQL
→ Verificar la estructura resultante
→ Registrar los cambios en Git
```

## Seguridad

Alembic utiliza la misma variable `DATABASE_URL` que el backend.

La contrasena de PostgreSQL permanece dentro de `.env`, que esta excluido del repositorio.

No se deben escribir credenciales dentro de:

- `alembic.ini`
- `migrations/env.py`
- Archivos de migracion
- README
- Commits
- Pull Requests