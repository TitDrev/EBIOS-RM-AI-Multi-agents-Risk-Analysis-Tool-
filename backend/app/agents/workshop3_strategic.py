"""Atelier 3 · Scénarios stratégiques (agent) : parties prenantes + scénarios cotés en gravité."""

from app.agents.base import run_json_workshop
from app.agents.cross_validation import attach_validation, sanitize_workshop_3
from app.agents.prompts import SECURITY_GUARD, WORKSHOP3_SYSTEM, build_workshop3_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import ScenariosStrategiquesOutput


async def run_workshop_3(state: AnalysisState) -> dict:
    """Exécute l'Atelier 3 : la gravité est cotée ici, la vraisemblance à l'Atelier 4."""
    user_prompt = build_workshop3_prompt(state)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP3_SYSTEM + SECURITY_GUARD, user_prompt, ScenariosStrategiquesOutput
    )
    data = model.model_dump(mode="json")
    data["_llm"] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    cleaned, issues = sanitize_workshop_3(data, state)
    return attach_validation(cleaned, issues)
