"""Tests unitaires du module de sécurité."""

import uuid

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("super-secret")
    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, "analyst")
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == "analyst"
