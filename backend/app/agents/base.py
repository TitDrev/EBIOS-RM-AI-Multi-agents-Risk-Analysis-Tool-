"""Helper commun pour l'exécution d'un atelier via un LLM."""

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.factory import get_llm_provider

T = TypeVar("T", bound=BaseModel)


async def run_json_workshop(
    system_prompt: str, user_prompt: str, schema: type[T]
) -> tuple[T, int, int]:
    """Appelle le LLM en mode JSON, valide la sortie contre `schema`.

    En cas de sortie invalide, retente avec un rappel ciblé du problème à corriger.
    Retourne (modèle validé, tokens_in, tokens_out) pour la traçabilité.
    """
    provider = get_llm_provider()
    prompt = user_prompt
    last_error: str | None = None
    tokens_in = tokens_out = 0

    for _ in range(3):
        data, tokens_in, tokens_out = await provider.complete_structured(system_prompt, prompt)
        if data is None:
            last_error = "Le LLM n'a pas produit de JSON valide."
            prompt = _append_format_reminder(user_prompt, schema, last_error)
            continue
        try:
            return schema.model_validate(data), tokens_in, tokens_out
        except ValidationError as exc:
            last_error = _format_errors(exc)
            prompt = _append_format_reminder(user_prompt, schema, last_error)

    raise ValueError(f"L'atelier n'a pas pu produire une sortie valide : {last_error}")


def _format_errors(exc: ValidationError) -> str:
    messages = []
    for e in exc.errors():
        loc = ".".join(str(x) for x in e["loc"])
        messages.append(f"{loc}: {e['msg']}")
    return "; ".join(messages)


def _append_format_reminder(user_prompt: str, schema: type[BaseModel], error: str) -> str:
    fields = list(schema.model_fields.keys())
    return (
        f"{user_prompt}\n\n"
        f"Ta réponse précédente était invalide : {error}\n"
        f"Corrige UNIQUEMENT les champs signalés et conserve tout le contenu déjà produit "
        f"(n'utilise pas de listes vides si des éléments ont été demandés). "
        f"Réponds en JSON avec exactement ces champs : {fields}."
    )
