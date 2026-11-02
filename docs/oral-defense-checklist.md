# Checklist para defensa oral

## Arquitectura

- Explicar la separacion Flutter, FastAPI y PostgreSQL.
- Mostrar inyeccion de dependencias en los servicios.
- Explicar por que la notificacion es secundaria a la persistencia.

## Seguridad

- JWT con algoritmo HS256 y expiracion configurable.
- Contrasenas almacenadas con Argon2.
- Codigos de recuperacion almacenados como HMAC, con vencimiento y limite de intentos.
- Respuesta generica para no revelar correos registrados.
- Secretos y credenciales fuera de Git.

## Reservas

- Validacion de horarios de sede.
- Prevencion de superposiciones.
- Cancelacion logica e historial.
- Identidad del usuario tomada del Bearer token.

## Notificaciones

- FID de Firebase Installation, no token deprecated.
- Solo dispositivos activos.
- Creacion y cancelacion toleran fallos de Firebase.
- Recordatorios cada cinco minutos y deduplicacion persistente.

## Flutter

- `runApp` no espera servicios push.
- `SessionGate` siempre muestra carga, login o sesion autenticada.
- `API_BASE_URL` permite usar URL de produccion sin perder `10.0.2.2` local.
- Las notificaciones en primer plano usan canal local de alta importancia.

## Evidencia

- Mostrar 473 pruebas backend pasando.
- Mostrar analisis y pruebas Flutter pasando.
- Mostrar APK release generado.
- Mostrar `alembic check` sin operaciones pendientes.
- Mostrar prueba manual de crear, cancelar y recordar una reserva.
