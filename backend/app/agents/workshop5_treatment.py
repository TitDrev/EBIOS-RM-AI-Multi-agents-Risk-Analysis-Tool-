"""Atelier 5 · Traitement du risque (agent)."""

from app.agents.base import run_json_workshop
from app.agents.cross_validation import attach_validation, sanitize_workshop_5
from app.agents.prompts import SECURITY_GUARD, WORKSHOP5_SYSTEM, build_workshop5_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import TraitementOutput
from app.tools.risk_math import compute_risk_level


async def run_workshop_5(state: AnalysisState) -> dict:
    """Exécute l'Atelier 5 et construit le registre des risques + plan de traitement."""
    user_prompt = build_workshop5_prompt(state)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP5_SYSTEM + SECURITY_GUARD, user_prompt, TraitementOutput,
        analysis_id=state.get("analysis_id"),
    )

    risques = []
    for risque in model.risques:
        data = risque.model_dump(mode="json")
        data["niveau"] = compute_risk_level(risque.vraisemblance, risque.gravite).value
        risques.append(data)

    data = {"risques": risques, "plan_traitement": model.plan_traitement,
            "_llm": {"tokens_in": tokens_in, "tokens_out": tokens_out}}
    cleaned, issues = sanitize_workshop_5(data, state)
    return attach_validation(cleaned, issues)
