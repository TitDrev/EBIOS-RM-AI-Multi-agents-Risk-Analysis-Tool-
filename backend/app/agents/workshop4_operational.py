"""Atelier 4 · Scénarios opérationnels (agent) : chemins d'attaque + vraisemblance."""

from app.agents.base import run_json_workshop
from app.agents.cross_validation import attach_validation, sanitize_workshop_4
from app.agents.prompts import SECURITY_GUARD, WORKSHOP4_SYSTEM, build_workshop4_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import ScenariosOperationnelsOutput
from app.tools.attack_techniques import all_techniques
from app.tools.risk_math import compute_risk_level


async def run_workshop_4(state: AnalysisState) -> dict:
    """Exécute l'Atelier 4 : vraisemblance évaluée ici, niveau calculé (matrice G×V)."""
    catalog = all_techniques()
    user_prompt = build_workshop4_prompt(state, catalog)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP4_SYSTEM + SECURITY_GUARD, user_prompt, ScenariosOperationnelsOutput
    )

    scenarios = []
    for scenario in model.scenarios_operationnels:
        niveau = compute_risk_level(scenario.vraisemblance, scenario.gravite)
        data = scenario.model_dump(mode="json")
        data["niveau"] = niveau.value
        scenarios.append(data)

    data = {"scenarios_operationnels": scenarios, "_llm": {"tokens_in": tokens_in, "tokens_out": tokens_out}}
    cleaned, issues = sanitize_workshop_4(data, state)
    return attach_validation(cleaned, issues)
