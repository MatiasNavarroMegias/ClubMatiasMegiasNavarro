from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Reservation


class ReservationRepository:
    """
    Administra la persistencia y las consultas de reservas.

    El repositorio concentra las expresiones de SQLAlchemy utilizadas
    por disponibilidad, proximas reservas, historial, superposiciones
    y cancelaciones.
    """

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        """
        Inicializa el repositorio con una sesion de SQLAlchemy.

        Args:
            database_session: Sesion utilizada para consultar y
                modificar informacion dentro de PostgreSQL.
        """
        self.database_session = database_session

    def get_by_id(
        self,
        reservation_id: int,
    ) -> Reservation | None:
        """
        Busca una reserva mediante su clave primaria.

        Args:
            reservation_id: Identificador interno de la reserva.

        Returns:
            La reserva encontrada o None cuando no existe.
        """
        return self.database_session.get(
            Reservation,
            reservation_id,
        )

    def get_by_id_and_user(
        self,
        *,
        reservation_id: int,
        user_id: int,
    ) -> Reservation | None:
        """
        Busca una reserva que pertenezca al usuario recibido.

        Esta consulta evita que un usuario consulte o cancele una
        reserva que pertenece a otra cuenta.

        Args:
            reservation_id: Identificador de la reserva.
            user_id: Identificador del usuario propietario.

        Returns:
            Reserva encontrada o None cuando no existe o no pertenece
            al usuario.
        """
        statement = select(Reservation).where(
            Reservation.id == reservation_id,
            Reservation.user_id == user_id,
        )

        return self.database_session.scalar(
            statement,
        )

    def get_overlapping_confirmed(
        self,
        *,
        sports_space_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> Reservation | None:
        """
        Busca una reserva confirmada que se superponga con el intervalo.

        Dos intervalos se superponen cuando la reserva existente
        comienza antes del final solicitado y termina despues del
        inicio solicitado.

        Esta formula permite que dos turnos consecutivos, por ejemplo
        18:00-19:00 y 19:00-20:00, no sean considerados superpuestos.

        Args:
            sports_space_id: Espacio que se desea reservar.
            start_at: Inicio solicitado.
            end_at: Finalizacion solicitada.
        Returns:
            La primera reserva superpuesta o None.
        """
        statement = select(Reservation).where(
            Reservation.sports_space_id == sports_space_id,
            Reservation.status == "confirmed",
            Reservation.start_at < end_at,
            Reservation.end_at > start_at,
        )

        return self.database_session.scalar(
            statement,
        )

    def list_confirmed_for_space_between(
        self,
        *,
        sports_space_id: int,
        range_start: datetime,
        range_end: datetime,
    ) -> list[Reservation]:
        """
        Lista reservas confirmadas que intersectan un rango temporal.

        Esta consulta se utilizara para calcular las horas ocupadas de
        un espacio durante una fecha determinada.

        Args:
            sports_space_id: Identificador del espacio deportivo.
            range_start: Inicio del rango consultado.
            range_end: Finalizacion del rango consultado.

        Returns:
            Reservas confirmadas ordenadas por horario de inicio.
        """
        statement = (
            select(Reservation)
            .where(
                Reservation.sports_space_id == sports_space_id,
                Reservation.status == "confirmed",
                Reservation.start_at < range_end,
                Reservation.end_at > range_start,
            )
            .order_by(
                Reservation.start_at,
            )
        )
        return list(
            self.database_session.scalars(
                statement,
            ).all(),
        )

    def list_upcoming_by_user(
        self,
        *,
        user_id: int,
        from_at: datetime,
    ) -> list[Reservation]:
        """
        Lista las reservas futuras confirmadas de un usuario.

        Args:
            user_id: Identificador del usuario propietario.
            from_at: Momento desde el que una reserva se considera
                futura.

        Returns:
            Reservas futuras ordenadas desde la mas cercana.
        """
        statement = (
            select(Reservation)
            .where(
                Reservation.user_id == user_id,
                Reservation.status == "confirmed",
                Reservation.start_at >= from_at,
            )
            .order_by(
                Reservation.start_at,
            )
        )
        return list(
            self.database_session.scalars(
                statement,
            ).all(),
        )

    def list_history_by_user(
        self,
        *,
        user_id: int,
        before_at: datetime,
    ) -> list[Reservation]:
        """
        Lista el historial de reservas de un usuario.

        El historial incluye reservas canceladas y reservas confirmadas
        cuyo horario ya finalizo.

        Args:
            user_id: Identificador del usuario propietario.
            before_at: Momento utilizado para identificar reservas
                finalizadas.

        Returns:
            Historial ordenado desde la reserva mas reciente.
        """
        statement = (
            select(Reservation)
            .where(
                Reservation.user_id == user_id,
                or_(
                    Reservation.status == "cancelled",
                    Reservation.end_at <= before_at,
                ),
            )
            .order_by(
                Reservation.start_at.desc(),
            )
        )

        return list(
            self.database_session.scalars(
                statement,
            ).all(),
        )

    def add(
        self,
        reservation: Reservation,
    ) -> Reservation:
        """
                    Persiste una nueva reserva.

        *   Args:
                reservation: Reserva que debe guardarse.

          * Returns:
                Reserva recargada con los valores generados por PostgreSQL.
        """
        self.database_session.add(
            reservation,
        )
        self.database_session.commit()
        self.database_session.refresh(
            reservation,
        )

        return reservation

    def save(
        self,
        reservation: Reservation,
    ) -> Reservation:
        """
        Confirma las modificaciones de una reserva existente.

        Este metodo se utilizara principalmente para guardar la
        cancelacion logica de una reserva.

        Args:
          reservation: Reserva previamente obtenida y modificada.

        Returns:
            Reserva actualizada despues de confirmar la transaccion.
        """
        self.database_session.commit()
        self.database_session.refresh(
            reservation,
        )

        return reservation
