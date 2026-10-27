from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import SportsSpace
from app.schemas import (
    SportsSpaceCreate,
    SportsSpaceResponse,
    SportsSpaceUpdate,
)


def test_sports_space_create_accepts_and_normalizes_valid_data() -> None:
    """
    Verifica la creacion y normalizacion de un espacio valido.
    """
    space_data = SportsSpaceCreate(
        venue_id=1,
        name=" Cancha de Futbol 1 ",
        sport_type=" futbol ",
        space_number=1,
    )

    assert space_data.venue_id == 1
    assert space_data.name == "Cancha de Futbol 1"
    assert space_data.sport_type == "Futbol"
    assert space_data.space_number == 1


def test_sports_space_create_rejects_invalid_venue_id() -> None:
    """
    Verifica que la sede tenga un identificador positivo.
    """
    with pytest.raises(ValidationError):
        SportsSpaceCreate(
            venue_id=0,
            name="Cancha de Futbol 1",
            sport_type="Futbol",
            space_number=1,
        )


def test_sports_space_create_rejects_invalid_space_number() -> None:
    """
    Verifica que el numero del espacio sea mayor que cero.
    """
    with pytest.raises(ValidationError):
        SportsSpaceCreate(
            venue_id=1,
            name="Cancha de Futbol 1",
            sport_type="Futbol",
            space_number=0,
        )


def test_sports_space_create_rejects_name_with_only_spaces() -> None:
    """
    Verifica que el nombre no contenga solamente espacios.
    """
    with pytest.raises(
        ValidationError,
        match="no puede contener solo espacios",
    ):
        SportsSpaceCreate(
            venue_id=1,
            name="   ",
            sport_type="Futbol",
            space_number=1,
        )


def test_sports_space_create_rejects_empty_sport_type() -> None:
    """
    Verifica que el tipo deportivo no contenga solamente espacios.
    """
    with pytest.raises(
        ValidationError,
        match="no puede contener solo espacios",
    ):
        SportsSpaceCreate(
            venue_id=1,
            name="Cancha 1",
            sport_type="   ",
            space_number=1,
        )


def test_sports_space_create_rejects_protected_fields() -> None:
    """
    Verifica que el cliente no pueda indicar campos internos.
    """
    protected_fields = (
        {"id": 99},
        {"is_active": False},
        {"created_at": "2026-10-24T12:00:00Z"},
        {"updated_at": "2026-10-24T12:00:00Z"},
    )

    for protected_field in protected_fields:
        with pytest.raises(ValidationError):
            SportsSpaceCreate(
                venue_id=1,
                name="Cancha de Futbol 1",
                sport_type="Futbol",
                space_number=1,
                **protected_field,
            )


def test_sports_space_update_accepts_partial_data() -> None:
    """
    Verifica que una actualizacion pueda contener un solo campo.
    """
    update_data = SportsSpaceUpdate(
        name=" Cancha Renovada ",
    )

    assert update_data.model_dump(exclude_unset=True) == {
        "name": "Cancha Renovada",
    }


def test_sports_space_update_normalizes_sport_type() -> None:
    """
    Verifica la normalizacion del deporte durante una actualizacion.
    """
    update_data = SportsSpaceUpdate(
        sport_type=" tenis ",
    )

    assert update_data.sport_type == "Tenis"


def test_sports_space_update_rejects_venue_change() -> None:
    """
    Verifica que un espacio no pueda trasladarse a otra sede.
    """
    with pytest.raises(
        ValidationError,
        match="Extra inputs are not permitted",
    ):
        SportsSpaceUpdate(
            venue_id=2,
        )


def test_sports_space_update_rejects_null_name() -> None:
    """
    Verifica que un nombre pueda omitirse, pero no enviarse como nulo.
    """
    with pytest.raises(
        ValidationError,
        match="no puede ser nulo",
    ):
        SportsSpaceUpdate(
            name=None,
        )


def test_sports_space_update_rejects_null_sport_type() -> None:
    """
    Verifica que el deporte no pueda enviarse como nulo.
    """
    with pytest.raises(
        ValidationError,
        match="no puede ser nulo",
    ):
        SportsSpaceUpdate(
            sport_type=None,
        )


def test_sports_space_update_rejects_invalid_space_number() -> None:
    """
    Verifica que una actualizacion mantenga un numero positivo.
    """
    with pytest.raises(ValidationError):
        SportsSpaceUpdate(
            space_number=-1,
        )


def test_sports_space_response_can_be_created_from_model() -> None:
    """
    Verifica la creacion de una respuesta desde SQLAlchemy.
    """
    audit_time = datetime(2026, 10, 24, 13, 30, tzinfo=UTC)

    sports_space = SportsSpace(
        id=1,
        venue_id=7,
        name="Cancha de Futbol 1",
        sport_type="Futbol",
        space_number=1,
        is_active=True,
        created_at=audit_time,
        updated_at=audit_time,
    )

    response = SportsSpaceResponse.model_validate(
        sports_space,
    )

    assert response.id == 1
    assert response.venue_id == 7
    assert response.name == "Cancha de Futbol 1"
    assert response.sport_type == "Futbol"
    assert response.space_number == 1
    assert response.is_active is True
    assert response.created_at == audit_time
    assert response.updated_at == audit_time


def test_sports_space_response_does_not_include_availability() -> None:
    """
    Verifica que la respuesta no publique disponibilidad estatica.
    """
    response_fields = set(
        SportsSpaceResponse.model_fields.keys(),
    )

    assert "is_available" not in response_fields
    assert "availability" not in response_fields
    assert "available" not in response_fields
