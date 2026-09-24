"""Modèle des scénarios stratégiques et opérationnels (Ateliers 3 & 4)."""

import uuid

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import GravityLevel, LikelihoodLevel, RiskLevel, ScenarioKind
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Scenario(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scenarios"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    kind: Mapped[ScenarioKind] = mapped_column(String(20))
    identifiant: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_risque_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    evenement_redoute_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    gravite: Mapped[GravityLevel | None] = mapped_column(String(20), nullable=True)
    vraisemblance: Mapped[LikelihoodLevel | None] = mapped_column(String(20), nullable=True)
    niveau: Mapped[RiskLevel | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
