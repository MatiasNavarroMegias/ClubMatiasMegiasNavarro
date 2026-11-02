# Checklist para defensa oral

## Objetivo y arquitectura

- Explicar que el sistema permite consultar sedes, reservar espacios
  deportivos y recibir avisos.
- Mostrar Flutter, FastAPI y PostgreSQL separados por API HTTPS.
- Explicar la inyeccion de dependencias y por que la persistencia no depende
  de que una notificacion secundaria sea exitosa.
- Indicar que Render aloja el servicio web y PostgreSQL administrado.

## Catalogo y reservas

- Mostrar cuatro sedes activas y 24 espacios, con tres deportes y dos
  espacios por deporte en cada sede.
- Explicar que `composite_code` es unico, generado por backend y regenerable.
- Explicar reservas de una o varias horas completas.
- Defender la zona horaria `America/Argentina/Buenos_Aires`.
- Explicar la formula de superposicion y el limite del horario de sede.
- Mostrar cancelacion logica, liberacion del horario e historial.

## Seguridad y errores

- JWT con algoritmo HS256 y expiracion configurable.
- Argon2 para contrasenas.
- Codigos de recuperacion almacenados como HMAC, con vencimiento y limite de
  intentos.
- Respuesta generica para evitar enumeracion de cuentas.
- Brevo por HTTPS en produccion: Render Free bloquea SMTP saliente.
- Si Brevo falla, el token se invalida y la API responde HTTP 503 sin stack
  trace, API key ni codigo.
- Secretos fuera de Git: Secret File de Firebase y variables secretas de
  Render.

## Notificaciones

- Firebase Installation ID para asociar instalaciones.
- Notificaciones de reserva confirmada y cancelada.
- Recordatorios cada cinco minutos mediante scheduler HTTPS externo.
- `reservation_reminders` garantiza deduplicacion.
- El endpoint interno requiere `X-Reminder-Secret`.

## Flutter

- `runApp` no espera servicios push bloqueantes.
- `SessionGate` resuelve login o sesion autenticada.
- `API_BASE_URL` permite alternar backend local y produccion.
- El APK tiene icono, splash y nombre visibles de Club Matias Megias Navarro.

## Evidencia

- Mostrar Swagger publico:
  <https://club-matias-megias-navarro-api.onrender.com/docs>.
- Mostrar `/health`, sedes, espacios, reserva y cancelacion.
- Mostrar recuperacion real mediante Brevo.
- Mostrar `502` tests backend y `186` tests Flutter.
- Mostrar `alembic current`, `alembic heads` y `alembic check`.
- Mostrar el APK en
  `mobile/build/app/outputs/flutter-apk/app-release.apk`.
