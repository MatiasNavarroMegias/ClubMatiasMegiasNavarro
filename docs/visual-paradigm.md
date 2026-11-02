# Material para Visual Paradigm

## Diagrama de clases del dominio

Crear las siguientes clases:

- `User`
- `Venue`
- `SportsSpace`
- `Reservation`
- `PasswordRecoveryToken`
- `PushDevice`
- `ReservationReminder`

Relacionarlas con estas multiplicidades:

```text
User 1 -------- 0..* Reservation
User 1 -------- 0..* PasswordRecoveryToken
User 1 -------- 0..* PushDevice
Venue 1 ------- 0..* SportsSpace
SportsSpace 1 - 0..* Reservation
Reservation 1 - 0..1 ReservationReminder
```

## Diagrama entidad-relacion

Usar PostgreSQL como sistema gestor y representar:

- claves primarias `id`;
- claves foraneas indicadas en `backend/docs/data-model.md`;
- `users.email` como unico;
- `push_devices.installation_id` como unico;
- `reservation_reminders.reservation_id` como unico;
- `sports_spaces.composite_code` como unico;
- `reservations.status` con valores `confirmed` y `cancelled`.

`SportsSpace.composite_code` es un identificador derivado regenerable. Se
actualiza cuando cambia el nombre o la direccion de `Venue`, o cuando cambia
el tipo o numero del espacio.

## Secuencia de crear reserva

1. `MobileApp` envia `POST /reservations` con Bearer token.
2. `FastAPI` obtiene `CurrentUser`.
3. `ReservationService` valida sede, espacio, horario y superposiciones.
4. `ReservationRepository` persiste la reserva.
5. `ReservationNotificationService` consulta dispositivos activos.
6. `FirebasePushSender` envia el aviso por FID.
7. La API devuelve la reserva creada aunque el paso 6 falle.

## Secuencia de recordatorio

1. Cron ejecuta `POST /internal/reminders` con `X-Reminder-Secret`.
2. El servicio consulta reservas confirmadas entre 55 y 65 minutos.
3. `ReservationReminderRepository` descarta reservas ya notificadas.
4. Se envia el aviso a los dispositivos activos.
5. Se registra `ReservationReminder` solamente despues del envio exitoso.
