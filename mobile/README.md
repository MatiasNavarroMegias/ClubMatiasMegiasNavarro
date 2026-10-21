# Aplicacion movil

Aplicacion Android de ClubMatiasMegiasNavarro desarrollada con Flutter.

## Requisitos

- Flutter 3.47 o superior.
- Dart 3.13 o superior.
- Android Studio.
- Android SDK.
- Emulador Android o dispositivo fisico.

## Recuperar las dependencias

Desde la carpeta `mobile`:

```powershell
flutter pub get
```

Este comando descarga las dependencias declaradas en `pubspec.yaml`.

## Analizar el codigo

```powershell
flutter analyze
```

El analisis estatico detecta errores y posibles problemas sin ejecutar la aplicacion.

## Ejecutar las pruebas

```powershell
flutter test
```

Las pruebas verifican que los widgets y comportamientos principales funcionen correctamente.

## Listar los emuladores disponibles

```powershell
flutter emulators
```

## Iniciar el emulador

```powershell
flutter emulators --launch Pixel_7
```

El identificador puede variar segun el dispositivo virtual configurado en Android Studio.

## Listar dispositivos conectados

```powershell
flutter devices --device-timeout 60
```

## Ejecutar la aplicacion

```powershell
flutter run
```

Para ejecutar en un dispositivo especifico:

```powershell
flutter run -d emulator-5554
```

El identificador debe coincidir con el valor mostrado por `flutter devices`.

## Estructura inicial

```text
lib/
├── main.dart
└── app/
    ├── app.dart
    └── theme/
        ├── app_colors.dart
        └── app_theme.dart
```

### `main.dart`

Es el punto de entrada de la aplicacion. Su unica responsabilidad es iniciar `ClubApp`.

### `app.dart`

Contiene el widget principal, la configuracion global y la pantalla inicial temporal.

### `app_colors.dart`

Centraliza la paleta de colores para evitar valores repetidos dentro de las pantallas.

### `app_theme.dart`

Construye los temas claro y oscuro a partir de la paleta general.

## Temas visuales

La aplicacion incluye:

- Tema claro.
- Tema oscuro.
- Seleccion automatica segun la configuracion del dispositivo.

La seleccion automatica se configura mediante:

```dart
themeMode: ThemeMode.system
```

## Detener la aplicacion

Durante la ejecucion de `flutter run`, presionar:

```text
q
```

Este comando finaliza la sesion de depuracion.

## Integracion con la API de sedes

La aplicacion movil se comunica con FastAPI mediante solicitudes HTTP.

El flujo de comunicacion es:

```text
Flutter
→ VenueApiClient
→ FastAPI
→ VenueService
→ VenueRepository
→ PostgreSQL
```

Flutter no se conecta directamente con PostgreSQL.

## Dependencia HTTP

El proyecto utiliza el paquete:

```yaml
http: ^1.6.0
```

Esta dependencia permite ejecutar solicitudes HTTP y utilizar clientes simulados durante las pruebas.

## Configuracion de la API

La direccion base se encuentra centralizada en:

```text
lib/core/config/api_config.dart
```

El valor predeterminado es:

```text
http://10.0.2.2:8000
```

El emulador Android utiliza `10.0.2.2` para acceder al servidor local de la computadora.

En Windows, FastAPI sigue disponible mediante:

```text
http://127.0.0.1:8000
```

## Reemplazar la direccion de la API

La direccion puede modificarse sin cambiar el codigo fuente:

```powershell
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

La configuracion utiliza:

```dart
String.fromEnvironment
```

Esto permite utilizar direcciones diferentes en desarrollo, pruebas y produccion.

## Modelo movil de sede

El modelo se encuentra en:

```text
lib/features/venues/data/models/venue.dart
```

La clase `Venue` representa la respuesta enviada por FastAPI.

Contiene:

```text
id
name
address
openingTime
closingTime
isActive
createdAt
updatedAt
```

### `Venue.fromJson`

Convierte una respuesta JSON de FastAPI en un objeto Dart.

Los nombres recibidos desde la API utilizan `snake_case`:

```json
{
  "opening_time": "08:00:00",
  "closing_time": "23:00:00",
  "is_active": true
}
```

El modelo Dart utiliza `camelCase`:

```text
openingTime
closingTime
isActive
```

### `toCreateJson`

Genera el cuerpo necesario para crear una sede.

No incluye:

```text
id
isActive
createdAt
updatedAt
```

Estos valores son administrados por FastAPI y PostgreSQL.

### `copyWith`

Genera una nueva instancia modificando solamente los valores indicados.

Esta operacion permite mantener objetos inmutables durante las actualizaciones de la interfaz.

## Cliente HTTP de sedes

El cliente se encuentra en:

```text
lib/features/venues/data/services/venue_api_client.dart
```

La clase `VenueApiClient` implementa:

```text
getVenues
getVenue
createVenue
updateVenue
```

### `getVenues`

Ejecuta:

```http
GET /venues
```

Devuelve:

```dart
Future<List<Venue>>
```

### `getVenue`

Ejecuta:

```http
GET /venues/{venue_id}
```

Devuelve una sede mediante su identificador.

### `createVenue`

Ejecuta:

```http
POST /venues
```

Envia nombre, direccion y horarios.

### `updateVenue`

Ejecuta:

```http
PATCH /venues/{venue_id}
```

Envia solamente los cambios recibidos.

Ejemplo:

```dart
{
  'name': 'Sede Ramos Mejia Centro',
}
```

## Manejo de errores

Los errores se representan mediante:

```dart
VenueApiException
```

La excepcion contiene:

```text
message
statusCode
```

Ejemplos:

```text
400 → la solicitud no contiene cambios
404 → la sede no existe
422 → los datos o los horarios son invalidos
null → no se pudo establecer una conexion
```

Cuando FastAPI devuelve un campo `detail`, el cliente conserva ese mensaje para que la interfaz pueda mostrarlo.

## Pruebas automatizadas

Las pruebas del modelo se encuentran en:

```text
test/features/venues/data/models/venue_test.dart
```

Verifican:

- Conversion desde JSON.
- Conversion de fechas.
- Generacion del JSON de creacion.
- Funcionamiento de `copyWith`.
- Inmutabilidad del objeto original.

Las pruebas del cliente se encuentran en:

```text
test/features/venues/data/services/venue_api_client_test.dart
```

Utilizan `MockClient` para verificar:

- Metodos HTTP.
- Direcciones solicitadas.
- Encabezados.
- Cuerpos JSON.
- Respuestas exitosas.
- Errores HTTP.
- JSON con estructura invalida.
- Fallos de conexion.

Las pruebas no necesitan iniciar FastAPI ni utilizar PostgreSQL.

## Ejecutar las verificaciones

Desde la carpeta `mobile`:

```powershell
dart format lib test
flutter analyze
flutter test
```

Resultado actual esperado:

```text
13 pruebas aprobadas
```

## Proxima integracion

El cliente sera utilizado por las pantallas de sedes para:

```text
Consultar sedes
→ mostrar el listado
→ seleccionar una sede
→ editar sus datos
→ guardar mediante PATCH
→ actualizar la interfaz
```

## Pantalla de listado de sedes

La pantalla `VenueListScreen` obtiene y muestra las sedes almacenadas en PostgreSQL mediante FastAPI.

El archivo se encuentra en:

```text
lib/features/venues/presentation/screens/venue_list_screen.dart
```

## Flujo completo

```text
Android Emulator
→ Flutter
→ VenueApiClient
→ FastAPI
→ VenueService
→ VenueRepository
→ SQLAlchemy
→ PostgreSQL
```

La integracion fue verificada utilizando datos reales almacenados en PostgreSQL.

## Informacion mostrada

Cada tarjeta de sede contiene:

- Nombre.
- Direccion.
- Horario de apertura.
- Horario de cierre.
- Estado activo o inactivo.
- Accion visual para consultar el detalle.

Los horarios recibidos desde FastAPI en formato:

```text
HH:mm:ss
```

se muestran en la interfaz como:

```text
HH:mm
```

## Estados de la pantalla

### Carga

Mientras se consulta la API, la pantalla muestra un indicador de progreso.

### Contenido

Cuando existen sedes, la pantalla muestra una tarjeta por cada registro recibido.

### Lista vacia

Cuando FastAPI devuelve una lista vacia, la pantalla muestra:

```text
No hay sedes disponibles
```

### Error de conexion

Cuando no se puede establecer una conexion con la API, la pantalla muestra:

```text
No se pudieron cargar las sedes
No se pudo establecer una conexion con la API.
```

Tambien muestra el boton:

```text
Reintentar
```

### Recuperacion

Si FastAPI vuelve a estar disponible, el boton `Reintentar` ejecuta una nueva solicitud y recupera el listado.

### Actualizacion manual

La pantalla utiliza `RefreshIndicator` para permitir una nueva consulta mediante el gesto de arrastre.

## Temas visuales

La pantalla utiliza los colores definidos por `ColorScheme`.

Esto permite conservar compatibilidad con:

- Tema claro.
- Tema oscuro.
- Tema configurado en el dispositivo.

## Administracion del cliente HTTP

`VenueListScreen` puede recibir un `VenueApiClient` mediante su constructor.

Durante la ejecucion normal, la pantalla crea el cliente y libera sus recursos cuando deja de utilizarse.

Durante las pruebas, puede recibir un cliente configurado con `MockClient` para evitar solicitudes HTTP reales.

## Pruebas de widgets

Las pruebas se encuentran en:

```text
test/features/venues/presentation/screens/venue_list_screen_test.dart
```

Verifican:

- Indicador de carga.
- Listado de sedes.
- Tarjetas activas e inactivas.
- Formato de horarios.
- Estado vacio.
- Estado de error.
- Boton de reintento.
- Recuperacion despues de un error.

La prueba principal de la aplicacion verifica la integracion:

```text
ClubApp
→ VenueListScreen
→ VenueApiClient simulado
```

## Verificacion real

FastAPI se inicio mediante:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Flutter utilizo desde Android Emulator:

```text
http://10.0.2.2:8000
```

La verificacion manual confirmo:

- Lectura de sedes reales.
- Respuestas `200 OK`.
- Visualizacion en Android Emulator.
- Error controlado cuando FastAPI no esta disponible.
- Recuperacion mediante el boton `Reintentar`.