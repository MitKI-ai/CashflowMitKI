"""JWT utilities — STORY-042"""
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_access_token(user_id: str, tenant_id: str, role: str) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    expire_minutes = settings.jwt_access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire_minutes * 60


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
