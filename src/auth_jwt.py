# src/auth_jwt.py
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET is required to use auth endpoints.")
    return secret


def create_access_token(
    *,
    subject: str,
    roles: list[str],
    department: str,
    ttl_minutes: int = 60,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    secret = get_jwt_secret()
    now = _now()

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
        "roles": roles,
        "department": department,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    secret = get_jwt_secret()
    return jwt.decode(token, secret, algorithms=["HS256"])
