# Material para Visual Paradigm

## Diagrama de clases y entidad-relacion

Representar estas entidades:

- `User`
- `Venue`
- `SportsSpace`
- `Reservation`
- `PasswordRecoveryToken`
- `PushDevice`
- `ReservationReminder`

Multiplicidades:

```text
User 1 -------- 0..* Reservation
User 1 -------- 0..* PasswordRecoveryToken
User 1 -------- 0..* PushDevice
Venue 1 ------- 0..* SportsSpace
SportsSpace 1 - 0..* Reservation
Reservation 1 - 0..1 ReservationReminder
```

Usar PostgreSQL como gestor y representar claves primarias `id`, claves
foraneas, unicidad de `users.email`, `push_devices.installation_id`,
`reservation_reminders.reservation_id` y
`sports_spaces.composite_code`.

`composite_code` es un identificador derivado, unico y regenerable. El
backend lo construye con sede, direccion, deporte y numero; normaliza
acentos y caracteres especiales y reemplaza espacios por guiones bajos.
Cambia si cambia alguno de esos datos y no se recibe desde Flutter.

## Secuencia de crear reserva

1. Flutter envia `POST /reservations`.
2. FastAPI obtiene el usuario desde el JWT.
3. `ReservationService` valida sede, espacio, horario, zona horaria y
   superposiciones.
4. `ReservationRepository` persiste la reserva.
5. Se consultan dispositivos activos.
6. Firebase Admin envia el aviso mediante FCM.
7. La API devuelve la reserva creada aunque falle el aviso secundario.

La fecha y los horarios se interpretan en
`America/Argentina/Buenos_Aires`. La duracion minima es una hora completa y
la hora final no puede superar el cierre de la sede.

## Secuencia de recordatorio

1. Un programador HTTPS externo ejecuta `POST /internal/reminders` cada cinco
   minutos con `X-Reminder-Secret`.
2. El servicio busca reservas confirmadas entre 55 y 65 minutos antes.
3. `ReservationReminderRepository` descarta reservas ya procesadas.
4. Firebase envia el aviso a los dispositivos activos.
5. El registro de deduplicacion se guarda solamente despues del envio exitoso.

## Recuperacion de contrasena

1. El usuario solicita un codigo mediante la API.
2. El backend guarda solamente un HMAC del codigo.
3. En produccion, `BrevoRecoveryCodeNotifier` llama por HTTPS a Brevo.
4. Un fallo externo invalida el token creado y devuelve HTTP 503 generico.
5. El endpoint no revela si el correo existe.
