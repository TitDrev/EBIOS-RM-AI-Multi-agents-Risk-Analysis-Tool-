"""Atelier 1 · Cadrage et socle de sécurité (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import WORKSHOP1_SYSTEM, build_user_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import CadrageOutput


async def run_workshop_1(state: AnalysisState) -> dict:
    """Exécute l'Atelier 1 et retourne la sortie structurée (CadrageOutput)."""
    user_prompt = build_user_prompt(state.get("si_description", {}))
    output = await run_json_workshop(WORKSHOP1_SYSTEM, user_prompt, CadrageOutput)
    return output.model_dump()
