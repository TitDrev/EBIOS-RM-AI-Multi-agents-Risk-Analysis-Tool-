"""Énumérations partagées du domaine (EBIOS RM)."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AnalysisStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    AWAITING_VALIDATION = "awaiting_validation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkshopStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_VALIDATION = "awaiting_validation"
    VALIDATED = "validated"
    CORRECTED = "corrected"
    FAILED = "failed"


class AssetKind(StrEnum):
    BIEN_ESSENTIEL = "bien_essentiel"
    BIEN_SUPPORT = "bien_support"


class SecurityNeed(StrEnum):
    DISPONIBILITE = "disponibilite"
    INTEGRITE = "integrite"
    CONFIDENTIALITE = "confidentialite"
    TRACABILITE = "tracabilite"


class RiskSourceType(StrEnum):
    ATTAQUANT_EXTERNE = "attaquant_externe"
    INTERNE_MALVEILLANT = "interne_malveillant"
    INTERNE_NEGLIGENT = "interne_negligent"
    SINISTRE_NATUREL = "sinistre_naturel"
    SINISTRE_ACCIDENTEL = "sinistre_accidentel"
    AUTRE = "autre"


class RiskSourceRelevance(StrEnum):
    RETENUE = "retenue"
    ECARTEE = "ecartee"
    A_SUIVRE = "a_suivre"


class ScenarioKind(StrEnum):
    STRATEGIQUE = "strategique"
    OPERATIONNEL = "operationnel"


class Level(StrEnum):
    """Échelle de gravité / vraisemblance (3 niveaux)."""

    FAIBLE = "faible"
    MOYEN = "moyen"
    ELEVE = "eleve"


class RiskLevel(StrEnum):
    """Niveau de risque issu de la matrice gravité × vraisemblance (4 niveaux)."""

    FAIBLE = "faible"
    MOYEN = "moyen"
    ELEVE = "eleve"
    CRITIQUE = "critique"


class Treatment(StrEnum):
    REDUIRE = "reduire"
    TRANSFERER = "transferer"
    EVITER = "eviter"
    ACCEPTER = "accepter"


class AgentRunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
