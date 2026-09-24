"""Schémas Pydantic pour les études EBIOS RM."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnalysisStatus


class AnalysisCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    si_description: dict = Field(default_factory=dict)


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    si_description: dict
    status: AnalysisStatus
    current_workshop: int
    threat_model: str | None = None
    created_at: datetime
