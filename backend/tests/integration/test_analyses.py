"""Tests d'intégration du flux analyses + ateliers + validation."""

import pytest


async def _register_and_token(client) -> str:
    await client.post(
        "/api/auth/register",
        json={"username": "analyst1", "email": "analyst1@example.com", "password": "supersecret1"},
    )
    resp = await client.post(
        "/api/auth/login/json",
        json={"username": "analyst1", "password": "supersecret1"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_start_validate_flow(client, mock_llm):
    token = await _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Création de l'étude
    resp = await client.post(
        "/api/analyses",
        json={
            "name": "Boutique en ligne",
            "si_description": {
                "nom": "Boutique en ligne",
                "ecosysteme": "Serveur web + base clients",
            },
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    analysis_id = resp.json()["id"]
    assert resp.json()["status"] == "draft"
    assert resp.json()["current_workshop"] == 0

    # Démarrage → Atelier 1 exécuté, en attente de validation
    resp = await client.post(f"/api/analyses/{analysis_id}/start", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["current_workshop"] == 1
    assert resp.json()["status"] == "awaiting_validation"

    # Consultation de l'atelier 1
    resp = await client.get(f"/api/analyses/{analysis_id}/workshops/1", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["numero"] == 1
    assert resp.json()["status"] == "awaiting_validation"
    assert "biens_essentiels" in resp.json()["output"]

    # Validation de l'atelier 1 → Atelier 2 (stub) produit
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/1/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 2
    assert resp.json()["status"] == "awaiting_validation"

    # Ressources de l'atelier 1 (biens, événements redoutés)
    resp = await client.get(f"/api/analyses/{analysis_id}/assets", headers=headers)
    assert resp.status_code == 200
    assert any(a["name"] == "Données clients" for a in resp.json())

    # Validation de l'atelier 2 → Atelier 3 produit
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/2/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 3

    resp = await client.get(f"/api/analyses/{analysis_id}/risk-sources", headers=headers)
    assert resp.status_code == 200
    assert resp.json()[0]["type"] == "attaquant_externe"

    # Validation de l'atelier 3 → Atelier 4 produit, scénarios persistés
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/3/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 4

    # Scénarios stratégiques persistés
    resp = await client.get(f"/api/analyses/{analysis_id}/scenarios", headers=headers)
    assert resp.status_code == 200
    strategiques = [s for s in resp.json() if s["kind"] == "strategique"]
    assert strategiques
    assert strategiques[0]["niveau"] == "eleve"

    # Validation de l'atelier 4 → Atelier 5 (stub) produit, scénarios opérationnels persistés
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/4/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 5

    resp = await client.get(f"/api/analyses/{analysis_id}/scenarios", headers=headers)
    operationnels = [s for s in resp.json() if s["kind"] == "operationnel"]
    assert operationnels
    assert operationnels[0]["identifiant"] == "O-01"


@pytest.mark.asyncio
async def test_validate_unstarted_workshop_conflicts(client, mock_llm):
    token = await _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/analyses",
        json={"name": "Étude vide", "si_description": {}},
        headers=headers,
    )
    analysis_id = resp.json()["id"]

    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/1/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 409
