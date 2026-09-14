import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.auth import SupabaseJWTVerifier
from app.config import Settings


@pytest.fixture
def signed_token(monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    verifier = SupabaseJWTVerifier(Settings(supabase_url="https://test.supabase.co"))
    monkeypatch.setattr(
        verifier.jwks, "get_signing_key_from_jwt",
        lambda _: SimpleNamespace(key=key.public_key()),
    )
    claims = dict(sub=str(uuid.uuid4()), iss=verifier.issuer, aud="authenticated",
                  exp=int(time.time()) + 300, role="authenticated")
    return verifier, key, claims


def test_valid_signature(signed_token):
    verifier, key, claims = signed_token
    token = jwt.encode(claims, key, algorithm="ES256")
    assert str(verifier.verify(token).id) == claims["sub"]


@pytest.mark.parametrize("changes", [
    {"exp": 1}, {"aud": "other"}, {"iss": "https://other.example/auth/v1"},
    {"role": "service_role"}, {"sub": "invalid"},
])
def test_invalid_claims(signed_token, changes):
    verifier, key, claims = signed_token
    with pytest.raises(HTTPException) as error:
        verifier.verify(jwt.encode(claims | changes, key, algorithm="ES256"))
    assert error.value.status_code == 401


def test_wrong_signature(signed_token):
    verifier, _, claims = signed_token
    key = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(HTTPException) as error:
        verifier.verify(jwt.encode(claims, key, algorithm="ES256"))
    assert error.value.status_code == 401
