"""Modèle des biens (essentiels et supports)."""

import uuid

from sqlalchemy import ARRAY, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AssetKind
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[AssetKind] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    besoins: Mapped[list] = mapped_column(ARRAY(String), default=list)
    value: Mapped[str | None] = mapped_column(String(20), nullable=True)
    supports: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
