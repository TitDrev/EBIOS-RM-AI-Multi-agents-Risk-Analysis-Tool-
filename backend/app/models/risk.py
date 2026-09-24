"""Modèle des risques (registre des risques, Atelier 5)."""

import uuid

from sqlalchemy import ARRAY, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import GravityLevel, LikelihoodLevel, RiskLevel, Treatment
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Risk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risks"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    identifiant: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gravite: Mapped[GravityLevel | None] = mapped_column(String(20), nullable=True)
    vraisemblance: Mapped[LikelihoodLevel | None] = mapped_column(String(20), nullable=True)
    niveau: Mapped[RiskLevel | None] = mapped_column(String(20), nullable=True)
    traitement: Mapped[Treatment | None] = mapped_column(String(20), nullable=True)
    mesures: Mapped[list] = mapped_column(ARRAY(String), default=list)
    risque_residuel: Mapped[RiskLevel | None] = mapped_column(String(20), nullable=True)
    sources: Mapped[list] = mapped_column(ARRAY(String), default=list)
    justification: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    valide_par: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
