"""Modèle des événements redoutés (Atelier 1)."""

import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import GravityLevel, SecurityNeed
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class FearedEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feared_events"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    label: Mapped[str] = mapped_column(String(500))
    bien_essentiel_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    besoin: Mapped[SecurityNeed | None] = mapped_column(String(30), nullable=True)
    gravite: Mapped[GravityLevel | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
