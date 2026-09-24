"""Fournisseur de test : retourne une réponse déterministe (aucun appel réseau)."""

from app.llm.base import LLMProvider, LLMResponse, LLMTool


class MockLLMProvider(LLMProvider):
    """Mock utilisé pour les tests et le développement hors connexion."""

    name = "mock"

    def __init__(self, fixed_response: str = '{"ok": true}'):
        self.fixed_response = fixed_response

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        return LLMResponse(content=self.fixed_response, tokens_in=10, tokens_out=10)
