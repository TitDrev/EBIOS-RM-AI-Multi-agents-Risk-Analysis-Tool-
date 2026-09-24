"""Modèle des sources de risques (Atelier 2)."""

import uuid

from sqlalchemy import ARRAY, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import GravityLevel, RiskSourceRelevance, RiskSourceType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RiskSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_sources"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    type: Mapped[RiskSourceType] = mapped_column(String(30))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    objectif: Mapped[str | None] = mapped_column(String(500), nullable=True)
    motivation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activite: Mapped[str | None] = mapped_column(String(500), nullable=True)
    capacite: Mapped[GravityLevel | None] = mapped_column(String(20), nullable=True)
    biens_vises: Mapped[list] = mapped_column(ARRAY(String), default=list)
    pertinence: Mapped[RiskSourceRelevance] = mapped_column(String(20), default=RiskSourceRelevance.RETENUE)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
