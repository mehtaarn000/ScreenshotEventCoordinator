import uuid

import pytest
from fastapi import HTTPException

from app.auth import SupabaseJWTVerifier
from app.config import Settings


def test_verifier_requires_supabase_url() -> None:
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        SupabaseJWTVerifier(Settings(supabase_url=None))


def test_verifier_rejects_malformed_token() -> None:
    verifier = SupabaseJWTVerifier(Settings(supabase_url="https://project.supabase.co"))
    with pytest.raises(HTTPException) as error:
        verifier.verify("not-a-jwt")
    assert error.value.status_code == 401


def test_current_user_requires_uuid_subject(monkeypatch) -> None:
    verifier = SupabaseJWTVerifier(Settings(supabase_url="https://project.supabase.co"))
    signing_key = type("SigningKey", (), {"key": "public-key"})()
    monkeypatch.setattr(verifier.jwks, "get_signing_key_from_jwt", lambda _: signing_key)
    monkeypatch.setattr(
        "app.auth.jwt.decode",
        lambda *_, **__: {
            "sub": "not-a-uuid",
            "role": "authenticated",
            "aud": "authenticated",
            "iss": verifier.issuer,
            "exp": 9999999999,
        },
    )
    with pytest.raises(HTTPException) as error:
        verifier.verify("token")
    assert error.value.status_code == 401


def test_current_user_is_built_from_verified_claims(monkeypatch) -> None:
    user_id = uuid.uuid4()
    verifier = SupabaseJWTVerifier(Settings(supabase_url="https://project.supabase.co"))
    signing_key = type("SigningKey", (), {"key": "public-key"})()
    monkeypatch.setattr(verifier.jwks, "get_signing_key_from_jwt", lambda _: signing_key)
    monkeypatch.setattr(
        "app.auth.jwt.decode",
        lambda *_, **__: {
            "sub": str(user_id),
            "email": "arnav@example.com",
            "role": "authenticated",
        },
    )

    user = verifier.verify("token")

    assert user.id == user_id
    assert user.email == "arnav@example.com"
