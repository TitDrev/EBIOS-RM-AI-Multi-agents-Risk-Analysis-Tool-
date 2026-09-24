"""Schémas Pydantic : sorties d'atelier et validation humaine."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator

from app.models.enums import (
    GravityLevel,
    LikelihoodLevel,
    RiskLevel,
    RiskSourceRelevance,
    RiskSourceType,
    SecurityNeed,
    Treatment,
    WorkshopStatus,
)
from app.schemas.validators import normalize_enum, normalize_gravity, normalize_likelihood

NormalizedGravity = Annotated[GravityLevel, BeforeValidator(normalize_gravity)]
NormalizedLikelihood = Annotated[LikelihoodLevel, BeforeValidator(normalize_likelihood)]
NormalizedNeed = Annotated[SecurityNeed, BeforeValidator(normalize_enum)]
NormalizedSourceType = Annotated[RiskSourceType, BeforeValidator(normalize_enum)]
NormalizedRelevance = Annotated[RiskSourceRelevance, BeforeValidator(normalize_enum)]
NormalizedRiskLevel = Annotated[RiskLevel, BeforeValidator(normalize_enum)]
NormalizedTreatment = Annotated[Treatment, BeforeValidator(normalize_enum)]


# --- Sortie de l'Atelier 1 « Cadrage et socle » ---

class BienEssentiel(BaseModel):
    name: str
    description: str = ""


class BienSupport(BaseModel):
    name: str
    description: str = ""
    supports: str = ""


class EvenementRedoute(BaseModel):
    bien_essentiel: str
    besoin: NormalizedNeed
    label: str
    gravite: NormalizedGravity


class MesureSocle(BaseModel):
    mesure: str
    referentiel: str = ""
    ecart: str | None = None


class Echelles(BaseModel):
    """Échelles EBIOS RM : gravité G1→G4, vraisemblance V1→V4."""

    gravite: list[str] = ["g1", "g2", "g3", "g4"]
    vraisemblance: list[str] = ["v1", "v2", "v3", "v4"]


class CadrageOutput(BaseModel):
    """Contrat JSON de sortie de l'Atelier 1."""

    perimetre: str = ""
    biens_essentiels: list[BienEssentiel] = []
    biens_supports: list[BienSupport] = []
    evenements_redoutes: list[EvenementRedoute] = []
    socle_securite: list[MesureSocle] = []
    echelles: Echelles = Echelles()

    @model_validator(mode="after")
    def _check_non_empty(self) -> "CadrageOutput":
        if not self.biens_essentiels:
            raise ValueError("La liste biens_essentiels ne doit pas être vide.")
        return self


# --- Sortie de l'Atelier 2 « Sources de risques » (menaces intentionnelles, couples SR/OV) ---

class SourceRisque(BaseModel):
    type: NormalizedSourceType
    name: str = ""
    objectif: str = ""
    motivation: str = ""
    activite: str = ""
    capacite: NormalizedGravity | None = None
    biens_vises: list[str] = []
    pertinence: NormalizedRelevance = RiskSourceRelevance.RETENUE
    description: str = ""


class SourcesRisquesOutput(BaseModel):
    sources_risques: list[SourceRisque] = []

    @model_validator(mode="after")
    def _check_non_empty(self) -> "SourcesRisquesOutput":
        if not self.sources_risques:
            raise ValueError("La liste sources_risques ne doit pas être vide.")
        return self


# --- Sortie de l'Atelier 3 « Scénarios stratégiques » (cote de gravité seule) ---

class ScenarioStrategique(BaseModel):
    identifiant: str
    source_risque: str
    evenement_redoute: str
    bien_essentiel: str = ""
    gravite: NormalizedGravity
    sources: list[str] = []


class PartiePrenante(BaseModel):
    name: str
    role: str = ""
    motif_criticite: str = ""


class ScenariosStrategiquesOutput(BaseModel):
    parties_prenantes: list[PartiePrenante] = []
    scenarios_strategiques: list[ScenarioStrategique] = []

    @model_validator(mode="after")
    def _check_non_empty(self) -> "ScenariosStrategiquesOutput":
        if not self.scenarios_strategiques:
            raise ValueError("La liste scenarios_strategiques ne doit pas être vide.")
        return self


# --- Sortie de l'Atelier 4 « Scénarios opérationnels » (vraisemblance évaluée ici) ---

class ScenarioOperationnel(BaseModel):
    identifiant: str
    scenario_strategique: str
    source_risque: str = ""
    evenement_redoute: str = ""
    chemin_attaque: list[str] = []
    biens_supports_impliques: list[str] = []
    techniques_attaque: list[str] = []
    gravite: NormalizedGravity
    vraisemblance: NormalizedLikelihood
    sources: list[str] = []

    @model_validator(mode="after")
    def _check_chemin(self) -> "ScenarioOperationnel":
        if not self.chemin_attaque:
            raise ValueError("Un scénario opérationnel doit avoir un chemin_attaque non vide.")
        return self


class ScenariosOperationnelsOutput(BaseModel):
    scenarios_operationnels: list[ScenarioOperationnel] = []

    @model_validator(mode="after")
    def _check_non_empty(self) -> "ScenariosOperationnelsOutput":
        if not self.scenarios_operationnels:
            raise ValueError("La liste scenarios_operationnels ne doit pas être vide.")
        return self


# --- Sortie de l'Atelier 5 « Traitement du risque » ---

class RisqueTraite(BaseModel):
    identifiant: str
    scenario_operationnel: str = ""
    scenario_strategique: str = ""
    bien_essentiel: str = ""
    evenement_redoute: str = ""
    source_risque: str = ""
    gravite: NormalizedGravity
    vraisemblance: NormalizedLikelihood
    niveau: NormalizedRiskLevel
    traitement: NormalizedTreatment
    mesures: list[str] = []
    risque_residuel: NormalizedRiskLevel
    justification: str = ""
    sources: list[str] = []
    valide_par: str | None = None


class TraitementOutput(BaseModel):
    risques: list[RisqueTraite] = []
    plan_traitement: str = ""

    @model_validator(mode="after")
    def _check_non_empty(self) -> "TraitementOutput":
        if not self.risques:
            raise ValueError("La liste risques ne doit pas être vide.")
        return self


# --- API workshops ---

class WorkshopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    numero: int
    status: WorkshopStatus
    output: dict
    corrections: list[str] = []
    validated_by: str | None = None
    validated_at: str | None = None
    created_at: datetime


class WorkshopValidate(BaseModel):
    corrections: list[str] = []
