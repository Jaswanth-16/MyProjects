"""Scoped, signed access tokens for SentinelForge's single-instance API.

Use a long random signing secret. This is not an OIDC replacement.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time


class TokenError(ValueError):
    pass


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(secret: str, subject: str, scope: str, *, ttl_seconds: int = 3600) -> str:
    if len(secret) < 32 or not subject.strip() or not scope.strip():
        raise ValueError("Signing secret must be >=32 characters; subject and scope are required")
    if ttl_seconds < 1 or ttl_seconds > 86400:
        raise ValueError("Token lifetime must be between 1 and 86400 seconds")
    payload = {"sub": subject, "scope": scope, "exp": int(time.time()) + ttl_seconds}
    body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + signature


def verify_token(secret: str, token: str) -> dict:
    try:
        body, signature = token.split(".")
        expected = _encode(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise TokenError("Invalid signature")
        payload = json.loads(_decode(body))
        if not isinstance(payload, dict) or not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise TokenError("Invalid subject")
        if not isinstance(payload.get("scope"), str) or not payload["scope"]:
            raise TokenError("Invalid scope")
        if type(payload.get("exp")) is not int or payload["exp"] <= int(time.time()):
            raise TokenError("Expired token")
        return payload
    except (ValueError, UnicodeDecodeError, KeyError, TypeError) as exc:
        raise TokenError("Invalid or expired token") from exc
