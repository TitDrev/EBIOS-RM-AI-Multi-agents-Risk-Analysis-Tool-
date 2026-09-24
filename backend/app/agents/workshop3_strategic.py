"""Atelier 3 · Scénarios stratégiques (agent) : parties prenantes + scénarios (gravité, vraisemblance initiale)."""

from app.agents.base import run_json_workshop
from app.agents.cross_validation import attach_validation, sanitize_workshop_3
from app.agents.prompts import SECURITY_GUARD, WORKSHOP3_SYSTEM, build_workshop3_prompt
from app.agents.state import AnalysisState
from app.models.enums import GravityLevel, LikelihoodLevel
from app.schemas.workshop import ScenariosStrategiquesOutput
from app.tools.risk_math import compute_risk_level


async def run_workshop_3(state: AnalysisState) -> dict:
    """Exécute l'Atelier 3 : gravité et vraisemblance initiale, niveau calculé (affiné à l'Atelier 4)."""
    user_prompt = build_workshop3_prompt(state)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP3_SYSTEM + SECURITY_GUARD,
        user_prompt,
        ScenariosStrategiquesOutput,
        analysis_id=state.get("analysis_id"),
    )
    data = model.model_dump(mode="json")
    for scenario in data.get("scenarios_strategiques", []):
        scenario["niveau"] = compute_risk_level(
            LikelihoodLevel(scenario["vraisemblance"]), GravityLevel(scenario["gravite"])
        ).value
    data["_llm"] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    cleaned, issues = sanitize_workshop_3(data, state)
    return attach_validation(cleaned, issues)
