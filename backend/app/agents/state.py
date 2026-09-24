"""État partagé du pipeline d'ateliers (LangGraph TypedDict)."""

from typing import TypedDict


class AnalysisState(TypedDict, total=False):
    analysis_id: str
    si_description: dict
    workshop_outputs: dict[int, dict]
    current_workshop: int
    knowledge_context: str
    workshop_corrections: list[str]
