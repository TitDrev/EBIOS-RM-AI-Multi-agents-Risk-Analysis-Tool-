"""Calcul du niveau de risque à partir de la matrice gravité × vraisemblance (EBIOS RM)."""

from app.models.enums import Level, RiskLevel

# Matrice : vraisemblance (lignes) × gravité (colonnes) → niveau de risque
_MATRIX: dict[Level, dict[Level, RiskLevel]] = {
    Level.ELEVE: {
        Level.FAIBLE: RiskLevel.MOYEN,
        Level.MOYEN: RiskLevel.ELEVE,
        Level.ELEVE: RiskLevel.CRITIQUE,
    },
    Level.MOYEN: {
        Level.FAIBLE: RiskLevel.FAIBLE,
        Level.MOYEN: RiskLevel.MOYEN,
        Level.ELEVE: RiskLevel.ELEVE,
    },
    Level.FAIBLE: {
        Level.FAIBLE: RiskLevel.FAIBLE,
        Level.MOYEN: RiskLevel.FAIBLE,
        Level.ELEVE: RiskLevel.MOYEN,
    },
}


def compute_risk_level(vraisemblance: Level, gravite: Level) -> RiskLevel:
    """Retourne le niveau de risque correspondant à la matrice EBIOS RM."""
    return _MATRIX[vraisemblance][gravite]
