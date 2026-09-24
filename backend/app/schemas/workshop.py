"""Schémas Pydantic : sorties d'atelier et validation humaine."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator

from app.models.enums import (
    Level,
    RiskSourceRelevance,
    RiskSourceType,
    SecurityNeed,
    WorkshopStatus,
)
from app.schemas.validators import normalize_enum

NormalizedLevel = Annotated[Level, BeforeValidator(normalize_enum)]
NormalizedNeed = Annotated[SecurityNeed, BeforeValidator(normalize_enum)]
NormalizedSourceType = Annotated[RiskSourceType, BeforeValidator(normalize_enum)]
NormalizedRelevance = Annotated[RiskSourceRelevance, BeforeValidator(normalize_enum)]


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
    gravite: NormalizedLevel


class MesureSocle(BaseModel):
    mesure: str
    referentiel: str = ""


class Echelles(BaseModel):
    gravite: list[str] = ["faible", "moyen", "eleve"]
    vraisemblance: list[str] = ["faible", "moyen", "eleve"]


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


# --- Sortie de l'Atelier 2 « Sources de risques » ---

class SourceRisque(BaseModel):
    type: NormalizedSourceType
    name: str = ""
    objectif: str = ""
    motivation: str = ""
    capacite: NormalizedLevel | None = None
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


# --- Sortie de l'Atelier 3 « Scénarios stratégiques » ---

class ScenarioStrategique(BaseModel):
    identifiant: str
    source_risque: str
    evenement_redoute: str
    bien_essentiel: str = ""
    gravite: NormalizedLevel
    vraisemblance: NormalizedLevel


class ScenariosStrategiquesOutput(BaseModel):
    scenarios_strategiques: list[ScenarioStrategique] = []

    @model_validator(mode="after")
    def _check_non_empty(self) -> "ScenariosStrategiquesOutput":
        if not self.scenarios_strategiques:
            raise ValueError("La liste scenarios_strategiques ne doit pas être vide.")
        return self


# --- Sortie de l'Atelier 4 « Scénarios opérationnels » ---

class ScenarioOperationnel(BaseModel):
    identifiant: str
    scenario_strategique: str
    source_risque: str = ""
    evenement_redoute: str = ""
    chemin_attaque: list[str] = []
    biens_supports_impliques: list[str] = []
    techniques_attaque: list[str] = []
    gravite: NormalizedLevel
    vraisemblance: NormalizedLevel


class ScenariosOperationnelsOutput(BaseModel):
    scenarios_operationnels: list[ScenarioOperationnel] = []

    @model_validator(mode="after")
    def _check_non_empty(self) -> "ScenariosOperationnelsOutput":
        if not self.scenarios_operationnels:
            raise ValueError("La liste scenarios_operationnels ne doit pas être vide.")
        return self


# --- API workshops ---

class WorkshopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    numero: int
    status: WorkshopStatus
    output: dict
    validated_by: str | None = None
    validated_at: str | None = None
    created_at: datetime


class WorkshopValidate(BaseModel):
    corrections: list[str] = []
