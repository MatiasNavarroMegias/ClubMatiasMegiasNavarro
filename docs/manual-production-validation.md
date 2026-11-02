# Validacion manual de produccion

## URLs publicas

- API: <https://club-matias-megias-navarro-api.onrender.com>
- Swagger: <https://club-matias-megias-navarro-api.onrender.com/docs>
- Health: <https://club-matias-megias-navarro-api.onrender.com/health>

## Comprobaciones basicas

1. Abrir `/health` y confirmar HTTP 200.
2. Abrir `/docs` y confirmar que Swagger carga.
3. Consultar `GET /venues` y confirmar cuatro sedes activas.
4. Consultar `GET /sports-spaces` y confirmar 24 espacios.
5. Confirmar tres tipos deportivos y dos espacios por tipo en cada sede.
6. Confirmar que cada `composite_code` no es nulo y es unico.

## Flujo de usuario

1. Ejecutar la aplicacion con:

   ```powershell
   flutter run -d emulator-5554 --dart-define=API_BASE_URL=https://club-matias-megias-navarro-api.onrender.com
   ```

2. Registrar una cuenta e iniciar sesion.
3. Editar nombre, apellido y fecha de nacimiento; confirmar que el correo no
   cambia.
4. Consultar sedes, filtrar deportes y elegir un espacio.
5. Crear una reserva de una hora.
6. Crear una reserva de varias horas completas.
7. Confirmar que se recibe la notificacion de reserva.
8. Intentar una superposicion y confirmar el rechazo.
9. Cancelar una reserva y confirmar que el horario queda libre y la reserva
   permanece en historial.
10. Cerrar sesion y comprobar que la pantalla publica vuelve a mostrarse.

## Recuperacion y notificaciones

- Solicitar recuperacion para una cuenta de prueba y recibir el correo
  mediante Brevo HTTPS.
- Confirmar un codigo correcto, un codigo vencido y el limite de intentos.
- Confirmar que un fallo del proveedor devuelve HTTP 503 generico y no deja
  un token utilizable.
- Confirmar notificaciones en primer plano y segundo plano.
- Ejecutar el programador HTTPS externo contra
  `POST /internal/reminders` con el secreto configurado, sin documentar el
  valor del secreto.
- Confirmar que una segunda ejecucion no duplica el recordatorio.

## Arranque y datos

El contenedor ejecuta:

```text
python -m alembic upgrade head
python -m app.scripts.seed_demo_data
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

La primera carga espera cuatro sedes y 24 espacios. Una nueva carga espera
`sedes creadas: 0` y `espacios creados: 0`. El seed no elimina ni modifica
usuarios, reservas, dispositivos, recordatorios ni secretos.

## APK

Generar con:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://club-matias-megias-navarro-api.onrender.com
```

Verificar:

`mobile/build/app/outputs/flutter-apk/app-release.apk`

Instalar el APK y repetir login, reserva, cancelacion y notificaciones sin
usar `flutter run`.

## Variables documentadas

Usar nombres sin valores reales:

```text
APP_ENV
APP_DEBUG
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
APP_TIMEZONE
FIREBASE_CREDENTIALS_PATH
FIREBASE_PROJECT_ID
REMINDER_INTERNAL_SECRET
RECOVERY_NOTIFIER_PROVIDER
BREVO_API_KEY
BREVO_FROM_EMAIL
BREVO_FROM_NAME
BREVO_API_URL
BREVO_TIMEOUT_SECONDS
```

`firebase-admin-key.json` se carga como Secret File en Render. No incluirlo
en Git ni en el APK. Render Free bloquea SMTP saliente; por eso Brevo usa
HTTPS. No documentar valores de secretos, FID, JWT, correos privados ni URLs
internas de PostgreSQL.
