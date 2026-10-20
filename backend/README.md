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

## Modelo de sede

El modelo `Venue` representa una sede deportiva almacenada en PostgreSQL.

La interfaz muestra el termino `Sede`, mientras que el codigo utiliza el nombre tecnico `Venue`.

La tabla fisica se llama:

```text
venues
```

## Campos de la sede

### `id`

Identificador interno y clave primaria de la sede.

PostgreSQL genera este valor automaticamente.

### `name`

Nombre visible de la sede.

```text
Tipo: VARCHAR(100)
Obligatorio: si
Indice: ix_venues_name
```

El indice permite optimizar futuras busquedas por nombre.

### `address`

Direccion fisica de la sede.

```text
Tipo: VARCHAR(200)
Obligatorio: si
```

La direccion admite una longitud mayor que el nombre porque puede contener calle, altura y otra informacion de ubicacion.

### `opening_time`

Hora de apertura habitual de la sede.

```text
Tipo: TIME
Obligatorio: si
```

No incluye una fecha porque representa un horario recurrente.

### `closing_time`

Hora de cierre habitual de la sede.

```text
Tipo: TIME
Obligatorio: si
```

La validacion que exige que el cierre sea posterior a la apertura se incorporara posteriormente en los esquemas y servicios.

### `is_active`

Indica si la sede se encuentra disponible dentro del sistema.

```text
Tipo: BOOLEAN
Obligatorio: si
Valor inicial: true
```

Una sede puede desactivarse sin eliminar su informacion ni perder futuras relaciones historicas.

### `created_at`

Fecha y hora de creacion del registro.

```text
Tipo: TIMESTAMP WITH TIME ZONE
Obligatorio: si
Valor inicial: now()
```

### `updated_at`

Fecha y hora de la ultima actualizacion del registro.

```text
Tipo: TIMESTAMP WITH TIME ZONE
Obligatorio: si
Valor inicial: now()
```

SQLAlchemy actualiza este valor cuando modifica el objeto.

## Archivos relacionados

```text
app/models/venue.py
tests/test_venue_model.py
migrations/versions/7ad3fe3fbc69_create_venues_table.py
```

### `app/models/venue.py`

Define como se representa y almacena una sede mediante SQLAlchemy.

### `tests/test_venue_model.py`

Verifica:

- El nombre de la tabla.
- El registro dentro de `Base.metadata`.
- Las columnas esperadas.
- Las restricciones de nulabilidad.
- Las longitudes de los textos.
- La construccion de objetos `Venue`.

### Migracion inicial

La revision:

```text
7ad3fe3fbc69
```

crea la tabla `venues` y el indice `ix_venues_name`.

La funcion `downgrade` elimina primero el indice y luego la tabla.

## Aplicar la migracion

Desde la carpeta `backend`:

```powershell
python -m alembic upgrade head
```

## Verificar la revision aplicada

```powershell
python -m alembic current
```

Resultado esperado:

```text
7ad3fe3fbc69 (head)
```

## Revertir la migracion

```powershell
python -m alembic downgrade -1
```

La migracion fue validada aplicando `upgrade`, ejecutando `downgrade` y aplicando nuevamente `upgrade head`.

## Esquemas de validacion de sede

Los esquemas Pydantic controlan los datos que recibe y devuelve la API.

El modelo SQLAlchemy `Venue` define como se almacena una sede en PostgreSQL, mientras que los esquemas definen:

- Que campos puede enviar el cliente.
- Que campos son obligatorios.
- Que limites deben respetarse.
- Que relaciones deben existir entre los valores.
- Que informacion devuelve la API.

Los esquemas se encuentran en:

```text
app/schemas/venue.py
```

## `VenueBase`

Contiene los campos compartidos por los esquemas de sede:

```text
name
address
opening_time
closing_time
```

### Reglas del nombre

```text
Longitud minima: 1 caracter
Longitud maxima: 100 caracteres
```

El limite coincide con la columna `name` del modelo SQLAlchemy.

### Reglas de la direccion

```text
Longitud minima: 1 caracter
Longitud maxima: 200 caracteres
```

El limite coincide con la columna `address` del modelo SQLAlchemy.

### Reglas de horarios

El horario de cierre debe ser posterior al horario de apertura:

```text
closing_time > opening_time
```

No se permiten:

- Horarios invertidos.
- Hora de apertura igual a la hora de cierre.
- Rangos sin duracion.

## `VenueCreate`

Representa los datos necesarios para crear una sede.

Ejemplo:

```json
{
  "name": "Sede Ramos Mejia",
  "address": "Avenida de Mayo 1000",
  "opening_time": "08:00:00",
  "closing_time": "23:00:00"
}
```

El cliente no envia:

```text
id
is_active
created_at
updated_at
```

Esos valores son administrados por el backend y PostgreSQL.

## `VenueUpdate`

Representa una actualizacion parcial de una sede.

Todos sus campos son opcionales porque se utilizara con el metodo HTTP `PATCH`.

Ejemplo de cambio de nombre:

```json
{
  "name": "Sede Ramos Mejia Centro"
}
```

Ejemplo de cambio de estado:

```json
{
  "is_active": false
}
```

Si se envian juntos `opening_time` y `closing_time`, el esquema valida inmediatamente su relacion.

Si se envia solamente uno de los horarios, la validacion final se realizara en el servicio despues de combinar el valor recibido con el horario almacenado en PostgreSQL.

## `VenueResponse`

Representa la informacion completa que la API devuelve al cliente.

Ejemplo:

```json
{
  "id": 1,
  "name": "Sede Ramos Mejia",
  "address": "Avenida de Mayo 1000",
  "opening_time": "08:00:00",
  "closing_time": "23:00:00",
  "is_active": true,
  "created_at": "2026-10-20T12:00:00Z",
  "updated_at": "2026-10-20T12:00:00Z"
}
```

El esquema utiliza:

```python
ConfigDict(from_attributes=True)
```

Esta configuracion permite construir una respuesta directamente desde una instancia SQLAlchemy de `Venue`.

## Pruebas de los esquemas

Las pruebas se encuentran en:

```text
tests/test_venue_schema.py
```

Las pruebas verifican:

- Creacion con datos validos.
- Rechazo de horarios invertidos.
- Rechazo de horarios iguales.
- Rechazo de nombres vacios.
- Rechazo de nombres mayores a 100 caracteres.
- Actualizaciones parciales.
- Validacion de horarios enviados juntos.
- Conversion desde un modelo SQLAlchemy.

## Diferencia entre modelo y esquema

```text
Modelo SQLAlchemy
→ representa la tabla y la persistencia en PostgreSQL

Esquema Pydantic
→ valida la entrada y construye la salida de la API
```

Esta separacion evita mezclar reglas de comunicacion HTTP con la estructura de almacenamiento.

## Repositorio de sedes

El repositorio de sedes centraliza las operaciones directas realizadas mediante SQLAlchemy.

El archivo se encuentra en:

```text
app/repositories/venue.py
```

La arquitectura prevista para las sedes es:

```text
Endpoint HTTP
→ Servicio con reglas de negocio
→ Repositorio con operaciones de persistencia
→ SQLAlchemy
→ PostgreSQL
```

Esta separacion evita que los endpoints construyan consultas o administren directamente las transacciones de la base de datos.

## `VenueRepository`

La clase `VenueRepository` recibe una sesion de SQLAlchemy mediante su constructor:

```python
VenueRepository(database_session)
```

El repositorio no crea ni cierra la sesion.

El ciclo de vida de la sesion es administrado por `get_db_session`, lo que permite utilizar una sesion independiente en cada solicitud HTTP.

## Operaciones disponibles

### `list_all`

Obtiene todas las sedes y solicita que PostgreSQL las ordene alfabeticamente por nombre.

```python
repository.list_all()
```

Resultado esperado:

```text
list[Venue]
```

La operacion utiliza una consulta construida mediante `select`.

### `get_by_id`

Busca una sede mediante su clave primaria.

```python
repository.get_by_id(venue_id)
```

Resultados posibles:

```text
Venue
None
```

El repositorio devuelve `None` cuando la sede no existe.

El repositorio no genera respuestas HTTP ni decide que codigo de error utilizar. Esa responsabilidad pertenecera posteriormente al servicio y al endpoint.

### `add`

Agrega una sede nueva a PostgreSQL.

La secuencia utilizada es:

```text
add
→ commit
→ refresh
```

`add` incorpora la nueva instancia a la sesion.

`commit` confirma la transaccion.

`refresh` recupera valores generados por PostgreSQL, como:

- Identificador.
- Fecha de creacion.
- Fecha de actualizacion.
- Valores predeterminados.

### `save`

Confirma las modificaciones realizadas sobre una sede existente.

La secuencia utilizada es:

```text
commit
→ refresh
```

No se ejecuta nuevamente `add` porque la instancia ya pertenece a la sesion que la obtuvo desde PostgreSQL.

## Responsabilidades que no pertenecen al repositorio

El repositorio no debe:

- Construir respuestas HTTP.
- Generar excepciones de FastAPI.
- Validar horarios de funcionamiento.
- Decidir si una sede puede modificarse.
- Convertir modelos en esquemas de respuesta.
- Administrar autenticacion o permisos.

Estas responsabilidades pertenecen a otras capas del backend.

## Pruebas del repositorio

Las pruebas se encuentran en:

```text
tests/test_venue_repository.py
```

Las pruebas utilizan `MagicMock` para simular una sesion de SQLAlchemy.

Esto permite verificar las interacciones del repositorio sin depender de:

- PostgreSQL iniciado.
- Credenciales locales.
- Datos de prueba almacenados.
- Una conexion real.
- Limpieza posterior de registros.

Las pruebas comprueban:

- Listado de sedes.
- Busqueda por identificador.
- Resultado de una sede inexistente.
- Creacion y confirmacion de una sede.
- Recarga de valores generados.
- Guardado de modificaciones.
- Ausencia de una llamada innecesaria a `add` durante una actualizacion.

## Diferencia entre repositorio y servicio

```text
Repositorio
→ realiza operaciones directas de persistencia

Servicio
→ aplica reglas de negocio y coordina operaciones
```

Por ejemplo, el repositorio puede obtener una sede por identificador.

El servicio decidira posteriormente que debe ocurrir si la sede no existe o si los horarios modificados no forman un rango valido.

## Servicio de sedes

El servicio de sedes concentra las reglas de negocio relacionadas con la creacion, consulta y actualizacion de sedes.

El archivo se encuentra en:

```text
app/services/venue.py
```

La arquitectura del modulo es:

```text
Endpoint HTTP
→ VenueService
→ VenueRepository
→ SQLAlchemy
→ PostgreSQL
```

## Responsabilidad del servicio

`VenueService` coordina:

- Los esquemas Pydantic.
- El modelo SQLAlchemy `Venue`.
- El repositorio de sedes.
- Las reglas de negocio.
- Las excepciones propias del dominio.

El servicio no construye respuestas HTTP ni utiliza `HTTPException`.

Esta separacion permite probar las reglas de negocio sin iniciar FastAPI.

## Operaciones disponibles

### `list_venues`

Obtiene todas las sedes disponibles mediante el repositorio.

```python
service.list_venues()
```

El orden de las sedes es responsabilidad del repositorio.

### `get_venue`

Busca una sede mediante su identificador.

```python
service.get_venue(venue_id)
```

Si la sede no existe, el servicio genera:

```python
VenueNotFoundError
```

El futuro endpoint traducira esta excepcion a una respuesta HTTP adecuada.

### `create_venue`

Crea un modelo `Venue` a partir de un esquema `VenueCreate`.

```python
service.create_venue(venue_data)
```

Una sede nueva se crea activa:

```python
is_active = True
```

El identificador y las fechas son administrados por PostgreSQL.

### `update_venue`

Modifica parcialmente una sede existente.

```python
service.update_venue(venue_id, venue_data)
```

La operacion utiliza:

```python
venue_data.model_dump(exclude_unset=True)
```

Esta configuracion permite identificar solamente los campos enviados realmente por el cliente.

## Actualizacion parcial con PATCH

Una solicitud puede modificar un unico campo:

```json
{
  "name": "Sede Ramos Mejia Centro"
}
```

Tambien puede modificar el estado:

```json
{
  "is_active": false
}
```

Los campos no enviados mantienen sus valores actuales.

## Deteccion de cambios efectivos

El servicio compara los valores recibidos con los valores almacenados.

Si la solicitud no contiene campos, genera:

```python
VenueNoChangesError
```

Si los valores recibidos coinciden con los valores actuales, tambien genera:

```python
VenueNoChangesError
```

Esta regla evita confirmar transacciones que no producen modificaciones reales.

## Validacion final de horarios

`VenueUpdate` puede recibir solamente uno de los horarios.

Ejemplo:

```json
{
  "closing_time": "07:00:00"
}
```

El esquema no puede validar completamente este caso porque no conoce el horario de apertura almacenado.

El servicio combina:

```text
Horario actual de apertura
+ nuevo horario de cierre
→ horario final
→ validacion
```

Si el cierre final no es posterior a la apertura, genera:

```python
InvalidVenueHoursError
```

Esta validacion protege las actualizaciones parciales.

## Excepciones del dominio

### `VenueNotFoundError`

Indica que no existe una sede con el identificador recibido.

### `VenueNoChangesError`

Indica que la solicitud no contiene modificaciones efectivas.

### `InvalidVenueHoursError`

Indica que el horario final de la sede no es valido.

Estas excepciones no dependen de FastAPI.

Los futuros endpoints seran responsables de convertirlas en respuestas HTTP.

## Pruebas del servicio

Las pruebas se encuentran en:

```text
tests/test_venue_service.py
```

Las pruebas utilizan un repositorio simulado mediante `MagicMock`.

Esto permite verificar las reglas de negocio sin depender de:

- PostgreSQL iniciado.
- Credenciales locales.
- Datos almacenados.
- Consultas SQL.
- Transacciones reales.

Las pruebas comprueban:

- Listado de sedes.
- Busqueda de una sede existente.
- Error por sede inexistente.
- Creacion de una sede activa.
- Actualizacion parcial.
- Solicitud sin campos.
- Valores iguales a los actuales.
- Horario parcial invalido.
- Horario parcial valido.
- Llamadas correctas al repositorio.

## Diferencia entre las capas

```text
Esquema Pydantic
→ valida el formato de entrada y salida

Servicio
→ aplica reglas de negocio

Repositorio
→ realiza operaciones de persistencia

Modelo SQLAlchemy
→ representa la tabla de PostgreSQL

Endpoint
→ recibe solicitudes y construye respuestas HTTP
```