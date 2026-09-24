"""Test d'intégration du flux d'authentification."""

import pytest


@pytest.mark.asyncio
async def test_register_login_me_flow(client):
    # Inscription
    resp = await client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret1"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["username"] == "alice"

    # Connexion (JSON)
    resp = await client.post(
        "/api/auth/login/json",
        json={"username": "alice", "password": "supersecret1"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    assert token

    # Profil
    resp = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post(
        "/api/auth/login/json",
        json={"username": "alice", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
