"""Adapter Opencode Go : client HTTP compatible OpenAI (chat completions)."""

import httpx

from app.config import settings
from app.llm.base import LLMProvider, LLMResponse, LLMTool


class OpencodeGoProvider(LLMProvider):
    """Fournisseur pointant vers un endpoint Opencode Go (compatible OpenAI)."""

    name = "opencode_go"

    def __init__(
        self,
        endpoint_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ):
        self.endpoint_url = (endpoint_url or settings.LLM_ENDPOINT_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LLM_API_KEY
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[LLMTool] | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload: dict = {"model": self.model, "messages": messages}
        # NB : `response_format={"type": "json_object"}` n'est PAS envoyé : sur cet
        # endpoint, il produit des réponses dégradées (clés espacées, wrapper schéma).
        # On s'appuie sur la consigne « JSON » des prompts + l'extraction robuste.
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        url = self.endpoint_url
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        content = message.get("content") or ""
        return LLMResponse(
            content=content,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            raw=data,
        )
