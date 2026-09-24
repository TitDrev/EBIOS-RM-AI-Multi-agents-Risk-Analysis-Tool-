"""Tests unitaires du calcul de niveau de risque (matrice EBIOS RM)."""

from app.models.enums import Level, RiskLevel
from app.tools.risk_math import compute_risk_level


def test_matrix_corners():
    assert compute_risk_level(Level.ELEVE, Level.ELEVE) == RiskLevel.CRITIQUE
    assert compute_risk_level(Level.FAIBLE, Level.FAIBLE) == RiskLevel.FAIBLE
    assert compute_risk_level(Level.ELEVE, Level.FAIBLE) == RiskLevel.MOYEN
    assert compute_risk_level(Level.FAIBLE, Level.ELEVE) == RiskLevel.MOYEN


def test_matrix_mid():
    assert compute_risk_level(Level.MOYEN, Level.MOYEN) == RiskLevel.MOYEN
    assert compute_risk_level(Level.MOYEN, Level.ELEVE) == RiskLevel.ELEVE
    assert compute_risk_level(Level.ELEVE, Level.MOYEN) == RiskLevel.ELEVE
