# Modelo de datos

Este documento define las entidades, atributos, relaciones y principales reglas de negocio de ClubMatiasMegiasNavarro.

El modelo utiliza PostgreSQL como base de datos relacional y SQLAlchemy como herramienta de mapeo objeto-relacional.

## Entidades principales

```text
User
Venue
SportsSpace
Reservation
PasswordRecoveryToken
PushDevice
ReservationReminder
```

## User

Representa una persona registrada en la aplicacion.

### Atributos

```text
id
first_name
last_name
birth_date
email
password_hash
is_active
created_at
updated_at
```

### Reglas

- El correo electronico identifica de forma unica a cada usuario.
- El correo no puede modificarse desde el perfil.
- La contrasena nunca se almacena en texto plano.
- El perfil debe incluir nombre, apellido y fecha de nacimiento.
- Una cuenta puede desactivarse sin eliminar sus reservas.
- Un usuario puede realizar varias reservas.
- Un usuario puede solicitar varios procesos de recuperacion de contrasena.
- Un usuario puede registrar varios dispositivos para notificaciones.

## Venue

Representa una sede del club.

### Atributos

```text
id
name
address
opening_time
closing_time
is_active
created_at
updated_at
```

### Reglas

- La sede debe tener nombre, direccion y horario de funcionamiento.
- El cierre debe ser posterior a la apertura.
- Una sede puede contener varios espacios deportivos.
- Una sede inactiva no debe ofrecer nuevos horarios de reserva.

## SportsSpace

Representa una cancha o espacio deportivo perteneciente a una sede.

### Atributos

```text
id
venue_id
space_type
number
name
is_active
created_at
updated_at
```

### Reglas

- Cada espacio deportivo pertenece a una unica sede.
- El tipo permite representar Futbol, Paddle, Basquet u otros deportes.
- El numero diferencia espacios del mismo tipo dentro de una sede.
- El nombre se construye utilizando sede, direccion, tipo y numero.

Ejemplo:

```text
Moron_Rivadavia_19850_Paddle_1
```

- Un espacio inactivo no puede recibir nuevas reservas.
- Los espacios pueden filtrarse por tipo.

## Reservation

Representa la reserva de un espacio deportivo realizada por un usuario.

### Atributos

```text
id
user_id
sports_space_id
reservation_date
start_time
end_time
status
created_at
updated_at
cancelled_at
```

### Estados sugeridos

```text
active
cancelled
```

Una reserva cuyo horario ya finalizo permanece activa como registro historico, salvo que haya sido cancelada.

### Reglas

- Una reserva pertenece a un usuario.
- Una reserva corresponde a un unico espacio deportivo.
- La fecha y el horario deben representar un momento futuro.
- La duracion minima es de una hora.
- El inicio y la finalizacion deben utilizar el minuto 00.
- La finalizacion debe ser posterior al inicio.
- El horario debe estar dentro del funcionamiento de la sede.
- La hora final no puede superar el cierre de la sede.
- No pueden existir reservas activas superpuestas para el mismo espacio y fecha.
- Una reserva cancelada libera nuevamente el horario.
- Las reservas finalizadas deben continuar visibles dentro del historial.

### Regla de superposicion

Existe superposicion cuando:

```text
nuevo_inicio < reserva_existente_fin
y
nuevo_fin > reserva_existente_inicio
```

Si ambas condiciones se cumplen, la reserva debe rechazarse.

## PasswordRecoveryToken

Representa una solicitud segura de recuperacion de contrasena.

### Atributos

```text
id
user_id
code_digest
expires_at
used_at
created_at
```

### Reglas

- El token enviado al usuario no se almacena directamente.
- PostgreSQL almacena solamente su hash.
- El token debe tener una fecha de vencimiento.
- Un token utilizado no puede volver a utilizarse.
- Un token vencido debe rechazarse.
- La recuperacion debe permitir establecer una nueva contrasena.

## PushDevice

Representa un dispositivo habilitado para recibir notificaciones push.

### Atributos

```text
id
user_id
installation_id
platform
is_active
created_at
updated_at
```

### Reglas

- Un usuario puede registrar varios dispositivos.
- El token identifica la aplicacion instalada en un dispositivo.
- El identificador corresponde al Firebase Installation ID utilizado por FCM.
- Un token puede desactivarse al cerrar sesion.
- La plataforma permite diferenciar Android de otras plataformas futuras.

## ReservationReminder

Registra que el recordatorio de una reserva ya fue enviado.

### Atributos

```text
id
reservation_id
sent_at
```

### Reglas

- Cada reserva confirmada puede tener como maximo un registro.
- El registro se crea solamente despues de enviar correctamente el aviso.
- Las reservas canceladas no se seleccionan para recordatorios.

## Relaciones

```text
User 1 -------- N Reservation
User 1 -------- N PasswordRecoveryToken
User 1 -------- N PushDevice
Reservation 1 - 0..1 ReservationReminder

Venue 1 ------- N SportsSpace

SportsSpace 1 - N Reservation
```

La sede de una reserva se obtiene mediante:

```text
Reservation
→ SportsSpace
→ Venue
```

## Integridad referencial

Las claves foraneas previstas son:

```text
sports_spaces.venue_id
→ venues.id

reservations.user_id
→ users.id

reservations.sports_space_id
→ sports_spaces.id

password_recovery_tokens.user_id
→ users.id

push_devices.user_id
→ users.id

reservation_reminders.reservation_id
→ reservations.id
```

## Identificacion del usuario autenticado

Las operaciones relacionadas con perfiles y reservas deben utilizar la identidad contenida en la sesion autenticada.

El cliente no debe poder indicar libremente otro `user_id` para:

- Crear una reserva.
- Consultar reservas personales.
- Cancelar una reserva.
- Consultar el perfil.
- Editar el perfil.

El backend obtiene el usuario desde el token de autenticacion.

## Consultas principales

El modelo debe permitir:

- Registrar usuarios.
- Iniciar sesion.
- Recuperar una contrasena.
- Consultar y editar el perfil.
- Listar sedes.
- Listar espacios de una sede.
- Filtrar espacios por tipo.
- Consultar disponibilidad.
- Crear una reserva.
- Listar reservas actuales.
- Cancelar una reserva.
- Consultar el historial.
- Asociar dispositivos para notificaciones.

## Desarrollo progresivo

Las entidades se implementaran en este orden:

```text
User
→ PasswordRecoveryToken
→ SportsSpace
→ Reservation
→ PushDevice
→ ReservationReminder
```

`Venue` ya se encuentra implementada y versionada mediante Alembic.