# ClubMatiasMegiasNavarro

Aplicación móvil para la gestión y reserva de espacios deportivos.

## Estado del proyecto

Proyecto en etapa inicial de configuración.

## Tecnologías previstas

- Flutter y Dart para la aplicación móvil.
- FastAPI y Python para la API REST.
- PostgreSQL como base de datos relacional.
- Firebase Authentication para autenticación.
- Firebase Cloud Messaging para notificaciones.
- Render para el despliegue en la nube.

## Despliegue

La configuracion inicial de Render se encuentra en [render.yaml](./render.yaml).
Incluye FastAPI en Docker, PostgreSQL administrado y las variables de entorno
necesarias sin credenciales reales. La cuenta de servicio Firebase y los
valores SMTP deben cargarse como secretos desde el panel del proveedor.
