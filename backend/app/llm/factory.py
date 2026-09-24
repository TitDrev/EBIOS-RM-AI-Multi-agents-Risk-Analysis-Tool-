"""Fabrique de fournisseur LLM selon la configuration."""

from functools import lru_cache

from app.config import settings
from app.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "mock":
        from app.llm.mock import MockLLMProvider

        return MockLLMProvider()

    from app.llm.opencode_go import OpencodeGoProvider

    return OpencodeGoProvider()
