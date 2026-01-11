# src/auth_passwords.py
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


# Argon2id (por defecto en argon2-cffi). Parámetros razonables para MVP.
_PH = PasswordHasher(
    time_cost=2,        # iteraciones
    memory_cost=102400, # ~100 MiB
    parallelism=8,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    password = (password or "").strip()
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return _PH.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _PH.verify(password_hash, password)
    except VerifyMismatchError:
        return False
