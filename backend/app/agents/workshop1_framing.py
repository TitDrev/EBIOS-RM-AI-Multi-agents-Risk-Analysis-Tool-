"""Atelier 1 · Cadrage et socle de sécurité (agent)."""

from app.agents.base import run_json_workshop
from app.agents.prompts import SECURITY_GUARD, WORKSHOP1_SYSTEM, build_user_prompt
from app.agents.state import AnalysisState
from app.schemas.workshop import CadrageOutput


async def run_workshop_1(state: AnalysisState) -> dict:
    """Exécute l'Atelier 1 et retourne la sortie structurée (CadrageOutput)."""
    user_prompt = build_user_prompt(state.get("si_description", {}), state)
    model, tokens_in, tokens_out = await run_json_workshop(
        WORKSHOP1_SYSTEM + SECURITY_GUARD, user_prompt, CadrageOutput
    )
    data = model.model_dump(mode="json")
    data["_llm"] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    return data
