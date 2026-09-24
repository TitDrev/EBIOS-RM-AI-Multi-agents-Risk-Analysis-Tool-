"""Tests unitaires de la couche LLM."""

import pytest

from app.llm.base import _extract_json
from app.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_provider_returns_fixed_response():
    provider = MockLLMProvider(fixed_response='{"message": "ok"}')
    resp = await provider.complete("system", "user")
    assert resp.content == '{"message": "ok"}'


@pytest.mark.asyncio
async def test_mock_provider_json_mode():
    provider = MockLLMProvider(fixed_response='{"a": 1}')
    result = await provider.complete_json("system", "user")
    assert result == {"a": 1}


def test_extract_json_plain():
    assert _extract_json('{"x": 1}') == {"x": 1}


def test_extract_json_fenced():
    assert _extract_json('```json\n{"x": 1}\n```') == {"x": 1}


def test_extract_json_with_noise():
    assert _extract_json('Voici le résultat : {"x": 1}. Merci.') == {"x": 1}


def test_extract_json_invalid():
    assert _extract_json("pas de json") is None


def test_extract_json_homoglyph_key():
    # La clé contient un "س" arabe au lieu du "s" latin.
    result = _extract_json('{"سources_risques": [{"type": "attaquant_externe"}]}')
    assert result == {"sources_risques": [{"type": "attaquant_externe"}]}


def test_extract_json_preserves_values():
    # Les VALEURS ne doivent pas être altérées (homoglyphes traités uniquement sur les clés).
    result = _extract_json('{"note": "200 μs et Серверы (Россия) restent intacts", "x": 1}')
    assert result == {"note": "200 μs et Серверы (Россия) restent intacts", "x": 1}


def test_extract_json_spaced_key():
    result = _extract_json('{"  sources_risques ": [1]}')
    assert result == {"sources_risques": [1]}
