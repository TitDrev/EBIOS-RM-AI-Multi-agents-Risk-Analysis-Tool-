"""Regroupe tous les modèles pour Alembic et l'importation."""

from app.models.agent_run import AgentRun
from app.models.analysis import Analysis
from app.models.asset import Asset
from app.models.feared_event import FearedEvent
from app.models.knowledge import KnowledgeDocument
from app.models.risk import Risk
from app.models.risk_source import RiskSource
from app.models.scenario import Scenario
from app.models.user import User
from app.models.workshop import Workshop

__all__ = [
    "AgentRun",
    "Analysis",
    "Asset",
    "FearedEvent",
    "KnowledgeDocument",
    "Risk",
    "RiskSource",
    "Scenario",
    "User",
    "Workshop",
]
