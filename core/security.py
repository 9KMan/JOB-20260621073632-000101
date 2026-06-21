"""Authentication helpers: JWT issuance/verification and bcrypt password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=get_settings().bcrypt_rounds,
)


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    if not plain:
        raise ValueError("password must not be empty")
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verify of a plaintext password against a stored hash."""
    if not plain or not hashed:
        return False
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """Issue a short-lived access token signed with HS256."""
    settings = get_settings()
    minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_days: Optional[int] = None,
) -> str:
    """Issue a longer-lived refresh token signed with HS256."""
    settings = get_settings()
    days = expires_days or settings.refresh_token_expire_days
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=days)).timestamp()),
        "type": "refresh",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """Decode and validate a JWT, optionally enforcing token type.

    Raises ``jose.JWTError`` on invalid signature, expiration, or wrong type.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise
    if expected_type and payload.get("type") != expected_type:
        raise JWTError(f"expected token type '{expected_type}', got '{payload.get('type')}'")
    return payload
