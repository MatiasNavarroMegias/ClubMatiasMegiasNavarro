from datetime import UTC, datetime, time

import pytest
from pydantic import ValidationError

from app.models import Venue
from app.schemas import VenueCreate, VenueResponse, VenueUpdate


def test_venue_create_accepts_valid_data() -> None:
    """
    Verifica que VenueCreate acepte una sede con datos validos.

    El horario de cierre es posterior al horario de apertura,
    y los datos de texto respetan las longitudes permitidas.
    """
    venue_data = VenueCreate(
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
    )

    assert venue_data.name == "Sede Ramos Mejia"
    assert venue_data.address == "Avenida de Mayo 1000"
    assert venue_data.opening_time == time(8, 0)
    assert venue_data.closing_time == time(23, 0)


def test_venue_create_rejects_invalid_operating_hours() -> None:
    """
    Verifica que el cierre no pueda ser anterior a la apertura.

    Esta validacion evita crear una sede con un rango horario
    invertido o imposible de utilizar para futuras reservas.
    """
    with pytest.raises(
        ValidationError,
        match="El horario de cierre debe ser posterior",
    ):
        VenueCreate(
            name="Sede Ramos Mejia",
            address="Avenida de Mayo 1000",
            opening_time=time(23, 0),
            closing_time=time(8, 0),
        )


def test_venue_create_rejects_equal_operating_hours() -> None:
    """
    Verifica que apertura y cierre no puedan tener la misma hora.

    Un rango con ambos horarios iguales no posee duracion y no
    permite ofrecer turnos dentro de la sede.
    """
    with pytest.raises(
        ValidationError,
        match="El horario de cierre debe ser posterior",
    ):
        VenueCreate(
            name="Sede Ramos Mejia",
            address="Avenida de Mayo 1000",
            opening_time=time(8, 0),
            closing_time=time(8, 0),
        )


def test_venue_create_rejects_empty_name() -> None:
    """
    Verifica que el nombre de la sede no pueda estar vacio.
    """
    with pytest.raises(ValidationError):
        VenueCreate(
            name="",
            address="Avenida de Mayo 1000",
            opening_time=time(8, 0),
            closing_time=time(23, 0),
        )


def test_venue_create_rejects_name_longer_than_limit() -> None:
    """
    Verifica que el nombre respete el limite de 100 caracteres.

    El limite coincide con la longitud configurada en la columna
    name del modelo SQLAlchemy.
    """
    with pytest.raises(ValidationError):
        VenueCreate(
            name="A" * 101,
            address="Avenida de Mayo 1000",
            opening_time=time(8, 0),
            closing_time=time(23, 0),
        )


def test_venue_update_accepts_partial_data() -> None:
    """
    Verifica que VenueUpdate permita modificar un solo campo.

    Esta caracteristica es necesaria porque el futuro endpoint PATCH
    recibira solamente los valores modificados por el usuario.
    """
    update_data = VenueUpdate(name="Sede Ramos Mejia Centro")

    assert update_data.name == "Sede Ramos Mejia Centro"
    assert update_data.address is None
    assert update_data.opening_time is None
    assert update_data.closing_time is None
    assert update_data.is_active is None


def test_venue_update_rejects_invalid_complete_hours() -> None:
    """
    Verifica los horarios cuando ambos se reciben en la actualizacion.

    Si se recibe solamente uno, la validacion final se realizara
    posteriormente al combinarlo con los datos almacenados.
    """
    with pytest.raises(
        ValidationError,
        match="El horario de cierre debe ser posterior",
    ):
        VenueUpdate(
            opening_time=time(20, 0),
            closing_time=time(8, 0),
        )


def test_venue_response_can_be_created_from_model() -> None:
    """
    Verifica que VenueResponse pueda leer una instancia SQLAlchemy.

    ConfigDict con from_attributes permite construir respuestas de
    la API directamente desde los atributos del modelo persistente.
    """
    creation_time = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    venue = Venue(
        id=1,
        name="Sede Ramos Mejia",
        address="Avenida de Mayo 1000",
        opening_time=time(8, 0),
        closing_time=time(23, 0),
        is_active=True,
        created_at=creation_time,
        updated_at=creation_time,
    )

    response = VenueResponse.model_validate(venue)

    assert response.id == 1
    assert response.name == "Sede Ramos Mejia"
    assert response.is_active is True
    assert response.created_at == creation_time
    assert response.updated_at == creation_time
