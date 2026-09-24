"""Normalisation des valeurs de niveau produites par le LLM.

Les LLM peuvent émettre des variantes (accents, synonymes, notation G1-G4 / V1-V4) :
« moyenne », « élevée », « G2 », « probable », etc. Ces fonctions ramènent les
valeurs à leur forme canonique avant validation Pydantic, afin de limiter les
rejets et les reprises.
"""

import unicodedata
from typing import Any

_GRAVITY_SYNONYMS = {
    "g1": "g1",
    "faible": "g1",
    "bas": "g1",
    "basse": "g1",
    "low": "g1",
    "g2": "g2",
    "moyen": "g2",
    "moyenne": "g2",
    "medium": "g2",
    "g3": "g3",
    "eleve": "g3",
    "elevee": "g3",
    "haute": "g3",
    "haut": "g3",
    "fort": "g3",
    "forte": "g3",
    "significatif": "g3",
    "g4": "g4",
    "critique": "g4",
    "tres_eleve": "g4",
    "tres_elevee": "g4",
    "extreme": "g4",
    "majeur": "g4",
    "majeure": "g4",
}

_LIKELIHOOD_SYNONYMS = {
    "v1": "v1",
    "rare": "v1",
    "faible": "v1",
    "improbable": "v1",
    "v2": "v2",
    "peu_probable": "v2",
    "moyen": "v2",
    "moyenne": "v2",
    "v3": "v3",
    "probable": "v3",
    "eleve": "v3",
    "elevee": "v3",
    "vraisemblable": "v3",
    "v4": "v4",
    "tres_probable": "v4",
    "tres_eleve": "v4",
    "certain": "v4",
    "certaine": "v4",
    "quasi_certain": "v4",
}


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        value = value.strip().lower().replace(" ", "_").replace("-", "_")
    return value


_ENUM_SYNONYMS = {
    "moyenne": "moyen",
    "elevee": "eleve",
    "retenu": "retenue",
    "a_suivre": "a_suivre",
    "confidentiel": "confidentialite",
    "dispo": "disponibilite",
    "integrite_": "integrite",
}


def normalize_enum(value: Any) -> Any:
    """Normalisation générique pour les énumérations simples (accents, espaces, synonymes)."""
    cleaned = _clean(value)
    if isinstance(cleaned, str):
        return _ENUM_SYNONYMS.get(cleaned, cleaned)
    return cleaned


def normalize_gravity(value: Any) -> Any:
    cleaned = _clean(value)
    if isinstance(cleaned, str):
        return _GRAVITY_SYNONYMS.get(cleaned, cleaned)
    return cleaned


def normalize_likelihood(value: Any) -> Any:
    cleaned = _clean(value)
    if isinstance(cleaned, str):
        return _LIKELIHOOD_SYNONYMS.get(cleaned, cleaned)
    return cleaned
