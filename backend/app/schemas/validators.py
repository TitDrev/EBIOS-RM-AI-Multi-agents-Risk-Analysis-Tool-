"""Normalisation des valeurs d'enum produites par le LLM.

Les LLM peuvent émettre des variantes (accents, féminin, synonymes) : « moyenne »,
« élevée », « Moyen », etc. Ces fonctions ramènent les valeurs à leur forme canonique
avant validation Pydantic, afin de limiter les rejets et les reprises.
"""

import unicodedata
from typing import Any

_SYNONYMS = {
    "moyenne": "moyen",
    "medium": "moyen",
    "elevee": "eleve",
    "elevated": "eleve",
    "haute": "eleve",
    "haut": "eleve",
    "fort": "eleve",
    "forte": "eleve",
    "basse": "faible",
    "bas": "faible",
    "low": "faible",
}


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        value = value.strip().lower().replace(" ", "_")
    return value


def normalize_enum(value: Any) -> Any:
    cleaned = _clean(value)
    if isinstance(cleaned, str):
        return _SYNONYMS.get(cleaned, cleaned)
    return cleaned
