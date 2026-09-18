from __future__ import annotations

import hashlib
import secrets


def generate_api_token() -> str:
    """Genereert een nieuw, willekeurig API-token (alleen bij aanmaak zichtbaar)."""
    return secrets.token_urlsafe(32)


def hash_api_token(token: str) -> str:
    """Zelfde patroon als password_hash: nooit het token zelf opslaan, alleen de hash."""
    return hashlib.sha256(token.encode()).hexdigest()
