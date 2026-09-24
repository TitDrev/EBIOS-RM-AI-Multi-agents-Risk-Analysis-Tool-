"""Calcul du niveau de risque à partir de la matrice gravité × vraisemblance (EBIOS RM).

Échelles : gravité G1→G4, vraisemblance V1→V4. La matrice 4×4 donne un niveau de
risque sur 4 classes : faible, moyen, élevé, critique.
"""

from app.models.enums import GravityLevel, LikelihoodLevel, RiskLevel

# Matrice : vraisemblance (lignes V1→V4) × gravité (colonnes G1→G4) → niveau de risque.
_MATRIX: dict[LikelihoodLevel, dict[GravityLevel, RiskLevel]] = {
    LikelihoodLevel.V1: {
        GravityLevel.G1: RiskLevel.FAIBLE,
        GravityLevel.G2: RiskLevel.FAIBLE,
        GravityLevel.G3: RiskLevel.MOYEN,
        GravityLevel.G4: RiskLevel.ELEVE,
    },
    LikelihoodLevel.V2: {
        GravityLevel.G1: RiskLevel.FAIBLE,
        GravityLevel.G2: RiskLevel.MOYEN,
        GravityLevel.G3: RiskLevel.ELEVE,
        GravityLevel.G4: RiskLevel.ELEVE,
    },
    LikelihoodLevel.V3: {
        GravityLevel.G1: RiskLevel.MOYEN,
        GravityLevel.G2: RiskLevel.MOYEN,
        GravityLevel.G3: RiskLevel.ELEVE,
        GravityLevel.G4: RiskLevel.CRITIQUE,
    },
    LikelihoodLevel.V4: {
        GravityLevel.G1: RiskLevel.MOYEN,
        GravityLevel.G2: RiskLevel.ELEVE,
        GravityLevel.G3: RiskLevel.CRITIQUE,
        GravityLevel.G4: RiskLevel.CRITIQUE,
    },
}


def compute_risk_level(vraisemblance: LikelihoodLevel, gravite: GravityLevel) -> RiskLevel:
    """Retourne le niveau de risque correspondant à la matrice gravité × vraisemblance."""
    return _MATRIX[vraisemblance][gravite]
