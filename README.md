# Club Matias Megias Navarro

Sistema movil para consultar sedes y espacios deportivos, reservar turnos y
recibir notificaciones de confirmacion, cancelacion y recordatorio.

## Arquitectura

```text
Flutter Android
    |
    | HTTPS / JSON
    v
FastAPI + SQLAlchemy
    |
    v
PostgreSQL administrado en Render
```

Firebase Admin se utiliza en el backend para enviar notificaciones mediante
Firebase Cloud Messaging. La cuenta de servicio se carga en Render como
Secret File y nunca se versiona. La recuperacion de contrasena utiliza Brevo
mediante su API HTTPS porque Render Free bloquea SMTP saliente.

## Tecnologias

- Flutter y Dart para la aplicacion Android.
- FastAPI y Python para la API REST.
- SQLAlchemy y Alembic para persistencia y migraciones.
- PostgreSQL en la nube mediante Render.
- JWT y Argon2 para autenticacion y contrasenas.
- Firebase Cloud Messaging para notificaciones.
- Brevo Transactional Email API para recuperacion de contrasena.
- Docker y Render para despliegue.

## Produccion

- API: <https://club-matias-megias-navarro-api.onrender.com>
- Swagger: <https://club-matias-megias-navarro-api.onrender.com/docs>
- Health check: <https://club-matias-megias-navarro-api.onrender.com/health>

La migracion vigente es `91c2d4e5f6a7`. El arranque del contenedor ejecuta
Alembic, el seed idempotente y Uvicorn en ese orden. Si falla una migracion o
el seed, la API no inicia.

El catalogo inicial contiene cuatro sedes activas y 24 espacios: seis por
sede, con tres deportes y dos espacios por deporte. Los espacios tienen un
`composite_code` unico generado por el backend a partir de sede, direccion,
tipo y numero.

Las reservas admiten una o varias horas completas, respetan el horario de
cada sede y usan `America/Argentina/Buenos_Aires`. La cancelacion es logica,
libera el horario y conserva la reserva en el historial. Los recordatorios se
procesan mediante `POST /internal/reminders` cada cinco minutos con un
programador HTTPS externo gratuito; `reservation_reminders` evita envios
duplicados.

## Desarrollo local

Backend:

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m alembic upgrade head
python -m app.scripts.seed_demo_data
python -m uvicorn app.main:app --reload
```

Mobile:

```powershell
cd mobile
flutter pub get
flutter run -d emulator-5554
```

## Ejecutar contra produccion

```powershell
cd mobile
flutter run -d emulator-5554 --dart-define=API_BASE_URL=https://club-matias-megias-navarro-api.onrender.com
```

## APK release

```powershell
cd mobile
flutter build apk --release --dart-define=API_BASE_URL=https://club-matias-megias-navarro-api.onrender.com
```

APK generado:

`mobile/build/app/outputs/flutter-apk/app-release.apk`

## Pruebas y evidencia

- Backend: 502 tests aprobados.
- Flutter: 186 tests aprobados.
- `flutter analyze` correcto.
- `alembic check` sin operaciones pendientes.
- Validacion manual contra la API publica, incluyendo registro, login,
  reservas, cancelacion, recuperacion por Brevo y notificaciones.

La configuracion local se documenta en [backend/README.md](./backend/README.md)
y [mobile/README.md](./mobile/README.md). El material de defensa se encuentra
en [docs/](./docs/).
