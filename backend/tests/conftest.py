"""Configuration des tests (base de données de test + overrides FastAPI)."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.database import Base, get_session

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://admin:admin@localhost:5433/risk_agents_test",
)

MOCK_CADRAGE_JSON = """
{
  "perimetre": "Système de démonstration",
  "biens_essentiels": [
    {"name": "Données clients", "description": "Données personnelles"}
  ],
  "biens_supports": [
    {"name": "Serveur web", "description": "Frontal HTTP", "supports": "Données clients"}
  ],
  "evenements_redoutes": [
    {"bien_essentiel": "Données clients", "besoin": "confidentialite",
     "label": "Fuite de données clients", "gravite": "eleve"}
  ],
  "socle_securite": [
    {"mesure": "Pare-feu", "referentiel": "ISO 27002"}
  ],
  "echelles": {"gravite": ["faible", "moyen", "eleve"], "vraisemblance": ["faible", "moyen", "eleve"]}
}
"""

MOCK_WORKSHOP2_JSON = """
{
  "sources_risques": [
    {"type": "attaquant_externe", "name": "Pirate", "objectif": "Vol de données",
     "motivation": "financière", "capacite": "eleve", "biens_vises": ["Données clients"],
     "pertinence": "retenue", "description": "Attaquant externe ciblant les données clients"}
  ]
}
"""

MOCK_WORKSHOP3_JSON = """
{
  "scenarios_strategiques": [
    {"identifiant": "S-01", "source_risque": "Pirate",
     "evenement_redoute": "Fuite de données clients", "bien_essentiel": "Données clients",
     "gravite": "eleve", "vraisemblance": "moyen"}
  ]
}
"""

MOCK_WORKSHOP4_JSON = """
{
  "scenarios_operationnels": [
    {"identifiant": "O-01", "scenario_strategique": "S-01", "source_risque": "Pirate",
     "evenement_redoute": "Fuite de données clients",
     "chemin_attaque": ["Scan du site", "Exploit d'une faille", "Exfiltration"],
     "biens_supports_impliques": ["Serveur web"],
     "techniques_attaque": ["T1190", "T1048"],
     "gravite": "eleve", "vraisemblance": "moyen"}
  ]
}
"""


class ConfigurableMockLLM:
    name = "mock"

    async def complete(self, system_prompt, user_prompt, tools=None, json_mode=False):
        from app.llm.base import LLMResponse

        if "ATELIER 2" in system_prompt:
            content = MOCK_WORKSHOP2_JSON
        elif "ATELIER 3" in system_prompt:
            content = MOCK_WORKSHOP3_JSON
        elif "ATELIER 4" in system_prompt:
            content = MOCK_WORKSHOP4_JSON
        else:
            content = MOCK_CADRAGE_JSON
        return LLMResponse(content=content, tokens_in=10, tokens_out=10)

    async def complete_json(self, system_prompt, user_prompt, tools=None):
        from app.llm.base import _extract_json

        resp = await self.complete(system_prompt, user_prompt, tools, json_mode=True)
        return _extract_json(resp.content)


@pytest.fixture
def mock_llm(monkeypatch):
    """Remplace le fournisseur LLM par un mock déterministe (aucun appel réseau)."""
    from app.agents import base as agents_base

    provider = ConfigurableMockLLM()
    monkeypatch.setattr(agents_base, "get_llm_provider", lambda: provider)
    return provider


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(test_session_factory):
    from app.main import app

    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
