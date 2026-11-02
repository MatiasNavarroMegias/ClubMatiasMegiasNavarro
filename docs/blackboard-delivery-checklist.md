# Checklist de entrega para Blackboard

## Material que se entrega

- Codigo fuente del proyecto.
- APK release:
  `mobile/build/app/outputs/flutter-apk/app-release.apk`.
- Modelo DER final en `docs/modelo-datos`.
- Documentacion de arquitectura, modelo, validacion y defensa.

## Descripcion breve

Club Matias Megias Navarro es una aplicacion Android para consultar cuatro
sedes, sus 24 espacios deportivos y reservar turnos. La API FastAPI y la
base PostgreSQL se encuentran desplegadas en Render.

## Evidencia tecnica

- API publica:
  <https://club-matias-megias-navarro-api.onrender.com>
- Swagger:
  <https://club-matias-megias-navarro-api.onrender.com/docs>
- Health check:
  <https://club-matias-megias-navarro-api.onrender.com/health>
- Migracion vigente: `91c2d4e5f6a7`.
- Backend: 502 tests aprobados.
- Flutter: 186 tests aprobados.
- APK release probado instalado sin `flutter run`.

## Demostracion recomendada

1. Abrir Swagger y consultar `/health`, `/venues` y `/sports-spaces`.
2. Ejecutar la aplicacion contra produccion.
3. Registrar una cuenta e iniciar sesion.
4. Editar el perfil sin modificar el correo.
5. Seleccionar una sede y filtrar espacios por deporte.
6. Crear una reserva de una hora y otra de varias horas.
7. Mostrar la notificacion de confirmacion.
8. Cancelar una reserva y mostrar que vuelve a estar disponible y queda en
   historial.
9. Solicitar recuperacion y mostrar el correo real recibido por Brevo sin
   exponer la API key ni el codigo en la documentacion.
10. Explicar el recordatorio, su endpoint protegido y la deduplicacion.

## Seguridad de la entrega

No incluir API keys, Secret Files, claves privadas, secretos internos,
contrasenas, JWT, FID reales, correos privados ni URLs internas de
PostgreSQL. Revisar `.gitignore` y `git diff --check` antes de comprimir o
compartir material.

## Limitaciones conocidas

Render Free puede suspender el servicio por inactividad y no permite cron
nativo ni Shell. Por eso el seed corre durante el arranque y los recordatorios
usan un programador HTTPS externo gratuito. Estas restricciones no cambian
las reglas de negocio.
