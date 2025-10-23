from __future__ import annotations
from typing import Any, Dict, Optional
from functools import lru_cache
import time
import json
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from .settings import settings

bearer_scheme = HTTPBearer(auto_error=False)

class JWKSCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl = ttl_seconds
        self._cached: Optional[Dict[str, Any]] = None
        self._expiry: float = 0.0

    def get(self, url: str) -> Dict[str, Any]:
        now = time.time()
        if self._cached is None or now >= self._expiry:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                self._cached = resp.json()
                self._expiry = now + self.ttl
        return self._cached  # type: ignore

_jwks_cache = JWKSCache(ttl_seconds=settings.AUTH0_JWKS_CACHE_MIN)


def _get_jwks() -> Dict[str, Any]:
    if not settings.AUTH0_DOMAIN:
        raise RuntimeError("AUTH0_DOMAIN not configured")
    url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    return _jwks_cache.get(url)


def _get_issuer() -> str:
    if settings.AUTH0_ISSUER:
        return settings.AUTH0_ISSUER
    if not settings.AUTH0_DOMAIN:
        raise RuntimeError("AUTH0_DOMAIN not configured for issuer")
    return f"https://{settings.AUTH0_DOMAIN}/"


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Dict[str, Any]:
    if settings.BYPASS_AUTH_FOR_TESTS:
        return {"sub": "test-user", "roles": ["admin"], "bypassed": True}

    if creds is None or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "missing_credentials"})

    token = creds.credentials
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        jwks = _get_jwks()
        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break
        if key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_kid"})

        issuer = _get_issuer()
        audience = settings.AUTH0_AUDIENCE
        algorithms = settings.AUTH0_ALGORITHMS or ["RS256"]
        payload = jwt.decode(token, key, algorithms=algorithms, audience=audience, issuer=issuer)

        roles = []
        # Standard Auth0 permissions or custom namespace claim
        if "permissions" in payload and isinstance(payload["permissions"], list):
            roles = payload["permissions"]
        for ns in ("https://nbne.io/roles", "https://example.com/roles", "roles"):
            v = payload.get(ns)
            if isinstance(v, list):
                roles = v
                break
        return {"sub": payload.get("sub"), "roles": roles, "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_token", "detail": str(e)})
