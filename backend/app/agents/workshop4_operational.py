"""Atelier 4 · Scénarios opérationnels (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import WORKSHOP4_SYSTEM, build_workshop4_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import ScenariosOperationnelsOutput
from app.tools.attack_techniques import all_techniques
from app.tools.risk_math import compute_risk_level


async def run_workshop_4(state: AnalysisState) -> dict:
    """Exécute l'Atelier 4 et calcule le niveau de risque de chaque scénario opérationnel."""
    catalog = all_techniques()
    user_prompt = build_workshop4_prompt(state, catalog)
    output = await run_json_workshop(
        WORKSHOP4_SYSTEM, user_prompt, ScenariosOperationnelsOutput
    )

    scenarios = []
    for scenario in output.scenarios_operationnels:
        niveau = compute_risk_level(scenario.vraisemblance, scenario.gravite)
        data = scenario.model_dump(mode="json")
        data["niveau"] = niveau.value
        scenarios.append(data)

    return {"scenarios_operationnels": scenarios}
