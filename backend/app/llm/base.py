"""Interface abstraite des fournisseurs de LLM."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMTool:
    """Outil exposé au LLM (lecture seule)."""

    name: str
    description: str
    parameters: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Réponse normalisée d'un appel LLM."""

    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    raw: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """Contrat unique pour tous les fournisseurs de LLM."""

    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Exécute un appel et retourne une réponse normalisée."""
        raise NotImplementedError

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
    ) -> dict[str, Any] | None:
        """Effectue un appel et tente de parser la réponse en JSON."""

        response = await self.complete(system_prompt, user_prompt, tools, json_mode=True)
        return _extract_json(response.content)

    async def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
    ) -> tuple[dict[str, Any] | None, int, int]:
        """Appel JSON avec retour de la réponse parsée et des tokens utilisés."""
        response = await self.complete(system_prompt, user_prompt, tools, json_mode=True)
        return _extract_json(response.content), response.tokens_in, response.tokens_out


def _extract_json(content: str) -> dict[str, Any] | None:
    """Extrait un objet JSON depuis le texte d'un LLM (tolérant aux fioritures).

    La normalisation des homoglyphes s'applique uniquement aux CLÉS du JSON parsé
    (jamais aux valeurs), ce qui évite d'altérer du contenu légitime (Cyrillique,
    symboles, etc.).
    """
    import json

    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    # 1) Essai direct sur tout le contenu (gère le JSON double-encodé en string).
    try:
        data = json.loads(content)
        return _normalize_keys(_unwrap_json(data))
    except json.JSONDecodeError:
        pass

    # 2) Extraction entre les premières/dernières accolades.
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return None
    return _normalize_keys(_unwrap_json(data))


def _normalize_keys(value: Any, depth: int = 0) -> Any:
    """Normalise récursivement les CLÉS d'un JSON (homoglyphes + espaces)."""
    if depth > 5:
        return value
    if isinstance(value, dict):
        return {
            _normalize_key(key): _normalize_keys(val, depth + 1)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_normalize_keys(item, depth + 1) for item in value]
    return value


def _normalize_key(key: str) -> str:
    if isinstance(key, str):
        return key.translate(_HOMOGLYPHS).strip()
    return key


def _unwrap_json(data: Any, depth: int = 0) -> Any:
    """Déballe un JSON double-encodé (le LLM renvoie parfois un JSON dans une string)."""
    if depth > 3 or not isinstance(data, str):
        return data
    stripped = data.strip()
    if stripped.startswith("{"):
        inner = _extract_json(stripped)
        return inner if inner is not None else data
    return data


# Homoglyphes courants (cyrillique, grec, arabe) ressemblant à des lettres latines.
_HOMOGLYPHS = str.maketrans(
    {
        # Cyrillique
        "а": "a", "в": "b", "с": "c", "е": "e", "о": "o", "р": "p", "х": "x",
        "у": "y", "к": "k", "м": "m", "н": "n", "т": "t",
        # Grec
        "α": "a", "β": "b", "ε": "e", "ο": "o", "ρ": "p", "σ": "s", "ς": "s",
        "τ": "t", "ν": "n", "μ": "m", "κ": "k", "ι": "i", "γ": "g",
        # Arabe (sous-ensemble)
        "س": "s", "ا": "a", "ي": "y",
    }
)
