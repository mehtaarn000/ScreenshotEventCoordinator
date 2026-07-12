import asyncio
import uuid
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError
from pydantic import BaseModel

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str | None = None
    role: str


class SupabaseJWTVerifier:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL is not configured")
        self.issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        self.audience = settings.supabase_jwt_audience
        self.jwks = PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True)

    def verify(self, token: str) -> CurrentUser:
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
            return CurrentUser(
                id=uuid.UUID(claims["sub"]),
                email=claims.get("email"),
                role=claims.get("role", "authenticated"),
            )
        except (InvalidTokenError, PyJWKClientError, KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc


@lru_cache
def get_jwt_verifier() -> SupabaseJWTVerifier:
    return SupabaseJWTVerifier(get_settings())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await asyncio.to_thread(get_jwt_verifier().verify, credentials.credentials)
