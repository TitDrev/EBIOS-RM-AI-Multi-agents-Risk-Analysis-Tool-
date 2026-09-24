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

    # Scénarios persistés : stratégiques + opérationnels
    resp = await client.get(f"/api/analyses/{analysis_id}/scenarios", headers=headers)
    assert resp.status_code == 200
    strategiques = [s for s in resp.json() if s["kind"] == "strategique"]
    operationnels = [s for s in resp.json() if s["kind"] == "operationnel"]
    assert strategiques
    # L'atelier 3 cote la gravité uniquement (la vraisemblance arrive à l'atelier 4)
    assert strategiques[0]["gravite"] == "g3"
    assert operationnels
    assert operationnels[0]["identifiant"] == "O-01"
    assert operationnels[0]["niveau"] == "critique"

    # Validation de l'atelier 4 → Atelier 5 produit (registre des risques)
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/4/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 5
    assert "risques" in resp.json()["output"]

    # Registre des risques persisté
    resp = await client.get(f"/api/analyses/{analysis_id}/risks", headers=headers)
    assert resp.status_code == 200
    assert resp.json()[0]["identifiant"] == "R-01"
    assert resp.json()[0]["traitement"] == "reduire"

    # Validation de l'atelier 5 → étude terminée
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/5/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "validated"

    resp = await client.get(f"/api/analyses/{analysis_id}", headers=headers)
    assert resp.json()["status"] == "completed"

    # Compte rendu JSON
    resp = await client.post(
        f"/api/analyses/{analysis_id}/report?format=json", headers=headers
    )
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["registre_des_risques"][0]["identifiant"] == "R-01"
    assert report["scenarios"]  # contient stratégiques + opérationnels

    # Compte rendu CSV
    resp = await client.post(
        f"/api/analyses/{analysis_id}/report?format=csv", headers=headers
    )
    assert resp.status_code == 200
    assert "identifiant" in resp.text
    assert "R-01" in resp.text


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


@pytest.mark.asyncio
async def test_correct_workshop_reruns_same_atelier(client, mock_llm):
    token = await _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/analyses",
        json={"name": "Boutique", "si_description": {"nom": "Boutique en ligne"}},
        headers=headers,
    )
    analysis_id = resp.json()["id"]
    await client.post(f"/api/analyses/{analysis_id}/start", headers=headers)

    # Correction de l'atelier 1 : relance SANS créer un doublon (toujours atelier 1).
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/1/correct",
        json={"corrections": ["Ajouter le bien 'Catalogue'"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["numero"] == 1
    assert resp.json()["status"] == "awaiting_validation"
    assert resp.json()["corrections"] == ["Ajouter le bien 'Catalogue'"]


@pytest.mark.asyncio
async def test_cannot_access_other_user_analysis(client, mock_llm):
    token = await _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/analyses",
        json={"name": "Étude secrète", "si_description": {}},
        headers=headers,
    )
    analysis_id = resp.json()["id"]

    # Deuxième utilisateur ne doit PAS accéder aux études du premier.
    await client.post(
        "/api/auth/register",
        json={"username": "viewer1", "email": "viewer1@example.com", "password": "supersecret1"},
    )
    resp = await client.post(
        "/api/auth/login/json", json={"username": "viewer1", "password": "supersecret1"}
    )
    other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = await client.get(f"/api/analyses/{analysis_id}", headers=other_headers)
    assert resp.status_code == 403

    resp = await client.get("/api/analyses", headers=other_headers)
    assert all(a["id"] != analysis_id for a in resp.json())


@pytest.mark.asyncio
async def test_compare_two_analyses(client, mock_llm):
    token = await _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    r1 = await client.post(
        "/api/analyses", json={"name": "étude 1", "si_description": {"nom": "s1"}}, headers=headers
    )
    a1 = r1.json()["id"]
    r2 = await client.post(
        "/api/analyses", json={"name": "étude 2", "si_description": {"nom": "s2"}}, headers=headers
    )
    a2 = r2.json()["id"]

    resp = await client.post(
        "/api/analyses/compare",
        json={"etude_a": a1, "etude_b": a2},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["etude_a"]["nom"] == "étude 1"
    assert body["etude_b"]["nom"] == "étude 2"
    assert "differences" in body
