"""Schémas de lecture des ressources EBIOS RM (biens, événements, sources, scénarios)."""

import uuid

from pydantic import BaseModel, ConfigDict


class RiskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identifiant: str | None = None
    gravite: str | None = None
    vraisemblance: str | None = None
    niveau: str | None = None
    traitement: str | None = None
    mesures: list = []
    risque_residuel: str | None = None
    sources: list = []
    justification: str | None = None
    valide_par: str | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: str
    description: str | None = None
    besoins: list = []
    value: str | None = None
    supports: str | None = None


class FearedEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    bien_essentiel_id: uuid.UUID | None = None
    besoin: str | None = None
    gravite: str | None = None


class RiskSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    name: str | None = None
    objectif: str | None = None
    motivation: str | None = None
    capacite: str | None = None
    biens_vises: list = []
    pertinence: str
    description: str | None = None


class ScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    identifiant: str | None = None
    gravite: str | None = None
    vraisemblance: str | None = None
    niveau: str | None = None
    description: str | None = None
    detail: dict = {}
