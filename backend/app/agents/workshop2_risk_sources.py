"""Atelier 2 · Sources de risques (agent) : menaces intentionnelles, couples SR/OV."""

from app.agents.base import run_json_workshop
from app.agents.cross_validation import attach_validation, sanitize_workshop_2
from app.agents.prompts import SECURITY_GUARD, WORKSHOP2_SYSTEM, build_workshop2_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import SourcesRisquesOutput


async def run_workshop_2(state: AnalysisState) -> dict:
    """Exécute l'Atelier 2 et retourne la liste des sources de risques (SR/OV)."""
    user_prompt = build_workshop2_prompt(state)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP2_SYSTEM + SECURITY_GUARD, user_prompt, SourcesRisquesOutput
    )
    data = model.model_dump(mode="json")
    data["_llm"] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    cleaned, issues = sanitize_workshop_2(data, state)
    return attach_validation(cleaned, issues)
