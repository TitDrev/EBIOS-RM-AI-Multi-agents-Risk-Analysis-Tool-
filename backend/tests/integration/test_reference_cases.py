"""Tests de bout en bout sur les cas de référence (A/B/C).

Pour chaque cas : création, lancement des 5 ateliers, validation humaine à chaque
étape, vérification de la complétude (registre des risques + compte rendu).
"""

import pytest

from app.reference_cases import REFERENCE_CASES


@pytest.mark.parametrize("case_id", list(REFERENCE_CASES))
async def test_reference_case_full_pipeline(client, mock_llm, case_id):
    case = REFERENCE_CASES[case_id]

    await client.post(
        "/api/auth/register",
        json={"username": f"analyst_{case_id}", "email": f"{case_id}@example.com", "password": "supersecret1"},
    )
    resp = await client.post(
        "/api/auth/login/json", json={"username": f"analyst_{case_id}", "password": "supersecret1"}
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/analyses",
        json={"name": case["label"], "si_description": case["si_description"]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    analysis_id = resp.json()["id"]

    await client.post(f"/api/analyses/{analysis_id}/start", headers=headers)
    for numero in range(1, 5):
        resp = await client.post(
            f"/api/analyses/{analysis_id}/workshops/{numero}/validate",
            json={"corrections": []},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    # L'atelier 5 contient le registre des risques
    resp = await client.get(f"/api/analyses/{analysis_id}/workshops/5", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["output"].get("risques")

    # Validation finale → étude terminée
    resp = await client.post(
        f"/api/analyses/{analysis_id}/workshops/5/validate",
        json={"corrections": []},
        headers=headers,
    )
    assert resp.status_code == 200
    detail = (await client.get(f"/api/analyses/{analysis_id}", headers=headers)).json()
    assert detail["status"] == "completed"

    # Compte rendu JSON exploitable
    report = (await client.post(f"/api/analyses/{analysis_id}/report?format=json", headers=headers)).json()
    assert report["registre_des_risques"]
    assert report["scenarios"]
    assert report["biens"]
