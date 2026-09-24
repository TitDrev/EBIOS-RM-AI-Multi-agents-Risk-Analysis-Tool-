"""Atelier 2 · Sources de risques (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import WORKSHOP2_SYSTEM, build_workshop2_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import SourcesRisquesOutput


async def run_workshop_2(state: AnalysisState) -> dict:
    """Exécute l'Atelier 2 et retourne la liste des sources de risques."""
    user_prompt = build_workshop2_prompt(state)
    output = await run_json_workshop(WORKSHOP2_SYSTEM, user_prompt, SourcesRisquesOutput)
    return output.model_dump(mode="json")
