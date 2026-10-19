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