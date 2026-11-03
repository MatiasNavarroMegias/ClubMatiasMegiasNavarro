import re
import unicodedata


def normalize_code_component(value: str) -> str:
    """
    Normaliza un componente para identificar espacios deportivos.

    Se eliminan acentos y caracteres especiales, los espacios se
    convierten en guiones bajos y se conserva la capitalizacion recibida.
    """
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    alphanumeric = re.sub(r"[^A-Za-z0-9]+", "_", without_accents)
    return alphanumeric.strip("_")


def build_sports_space_code(
    *,
    venue_name: str,
    venue_address: str,
    sport_type: str,
    space_number: int,
) -> str:
    """Construye el codigo publico unico de un espacio deportivo."""
    components = (
        venue_name,
        venue_address,
        sport_type,
        str(space_number),
    )
    return "_".join(normalize_code_component(component) for component in components)
