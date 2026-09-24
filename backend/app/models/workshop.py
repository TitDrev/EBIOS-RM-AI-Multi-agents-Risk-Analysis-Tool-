"""Modèle de l'état et de la validation de chaque atelier."""

import uuid

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import WorkshopStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Workshop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workshops"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    numero: Mapped[int] = mapped_column(index=True)
    status: Mapped[WorkshopStatus] = mapped_column(String(30), default=WorkshopStatus.PENDING)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    validated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    corrections: Mapped[list] = mapped_column(JSON, default=list)
