"""Smoke-test de l'endpoint LLM Opencode Go.

Usage :
    .venv/bin/python scripts/smoke_llm.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm.factory import get_llm_provider


async def main() -> None:
    provider = get_llm_provider()
    print(f"Provider : {provider.name}")

    resp = await provider.complete(
        system_prompt="Tu es un assistant concis.",
        user_prompt="Réponds en une phrase : quelle est la première étape de la méthode EBIOS RM ?",
    )
    print("--- simple ---")
    print(resp.content.strip())
    print(f"tokens_in={resp.tokens_in} tokens_out={resp.tokens_out}")

    data = await provider.complete_json(
        system_prompt="Tu réponds uniquement en JSON.",
        user_prompt='Retourne le JSON {"atelier": 1, "nom": "Cadrage et socle de sécurité"}.',
    )
    print("--- json_mode ---")
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
