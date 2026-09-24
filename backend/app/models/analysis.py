"""Modèle d'étude EBIOS RM (une analyse de risques d'un SI)."""

import uuid

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AnalysisStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    name: Mapped[str] = mapped_column(String(255))
    si_description: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[AnalysisStatus] = mapped_column(String(30), default=AnalysisStatus.DRAFT)
    current_workshop: Mapped[int] = mapped_column(default=0)
    threat_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
