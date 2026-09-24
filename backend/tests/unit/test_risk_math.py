"""Tests unitaires du calcul de niveau de risque (matrice EBIOS RM 4×4)."""

from app.models.enums import GravityLevel, LikelihoodLevel, RiskLevel
from app.tools.risk_math import compute_risk_level


def test_matrix_corners():
    assert compute_risk_level(LikelihoodLevel.V1, GravityLevel.G1) == RiskLevel.FAIBLE
    assert compute_risk_level(LikelihoodLevel.V4, GravityLevel.G4) == RiskLevel.CRITIQUE
    assert compute_risk_level(LikelihoodLevel.V4, GravityLevel.G1) == RiskLevel.MOYEN
    assert compute_risk_level(LikelihoodLevel.V1, GravityLevel.G4) == RiskLevel.ELEVE


def test_matrix_mid():
    assert compute_risk_level(LikelihoodLevel.V2, GravityLevel.G2) == RiskLevel.MOYEN
    assert compute_risk_level(LikelihoodLevel.V3, GravityLevel.G3) == RiskLevel.ELEVE
    assert compute_risk_level(LikelihoodLevel.V3, GravityLevel.G4) == RiskLevel.CRITIQUE
