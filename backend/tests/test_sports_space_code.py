from app.core.normalization import build_sports_space_code, normalize_code_component


def test_normalize_code_component_removes_accents_spaces_and_symbols() -> None:
    assert normalize_code_component("Rivadavia 19.850 (Norte)") == "Rivadavia_19_850_Norte"
    assert normalize_code_component("Páddle") == "Paddle"


def test_build_sports_space_code_matches_required_format() -> None:
    assert (
        build_sports_space_code(
            venue_name="Morón",
            venue_address="Rivadavia 19850",
            sport_type="Páddle",
            space_number=1,
        )
        == "Moron_Rivadavia_19850_Paddle_1"
    )
