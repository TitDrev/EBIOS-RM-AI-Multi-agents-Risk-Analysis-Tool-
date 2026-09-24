"""Modèle de trace d'exécution d'un atelier (agent)."""

import uuid

from sqlalchemy import JSON, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AgentRunStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    agent: Mapped[str] = mapped_column(String(100))
    workshop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    input_snapshot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[AgentRunStatus] = mapped_column(String(20), default=AgentRunStatus.RUNNING)
