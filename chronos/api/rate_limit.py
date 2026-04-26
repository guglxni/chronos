"""Centralized SlowAPI limiter configuration for CHRONOS.

The key function resolves the "real" remote IP with two modes:

- **Direct mode (default):** use the ASGI ``client`` tuple from uvicorn.  This
  is trustworthy because it's the TCP peer address — not a header the caller
  can set.
- **Proxied mode (``TRUST_PROXY_HEADERS=true``):** walk ``X-Forwarded-For``
  from the *right* side, skipping addresses present in
  ``TRUSTED_PROXY_IPS``.  Falls through to the TCP peer if no untrusted IP is
  found.

``get_remote_address`` from slowapi itself naively trusts ``X-Forwarded-For``
without configuration, so a single attacker can spin up unlimited rate-limit
buckets by varying the header.  This module fixes that.

Configure via ``TRUST_PROXY_HEADERS`` and ``TRUSTED_PROXY_IPS`` env vars; when
unset (the hackathon default), the TCP peer is used directly.
"""
from __future__ import annotations

import os

from slowapi import Limiter
from starlette.requests import Request


def _parse_trusted_proxies() -> frozenset[str]:
    raw = os.environ.get("TRUSTED_PROXY_IPS", "")
    return frozenset(addr.strip() for addr in raw.split(",") if addr.strip())


_TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "").lower() in {
    "1", "true", "yes",
}
_TRUSTED_PROXY_IPS = _parse_trusted_proxies()


def _rate_limit_key(request: Request) -> str:
    """
    Derive the rate-limit key from the request.

    Security: in direct mode, the key is the TCP peer from ``request.client`` —
    cannot be spoofed.  In proxied mode, X-Forwarded-For is consulted only when
    the immediate peer is a trusted proxy; otherwise we fall back to the peer.
    """
    tcp_peer = request.client.host if request.client else "unknown"

    if not _TRUST_PROXY_HEADERS or tcp_peer not in _TRUSTED_PROXY_IPS:
        return tcp_peer

    xff = request.headers.get("x-forwarded-for", "")
    if not xff:
        return tcp_peer

    # Walk right-to-left, stopping at the first address NOT in the trusted set.
    # (Rightmost entries are the proxies we added ourselves; the leftmost is
    # the original client, which may be spoofable.)
    for raw in reversed([p.strip() for p in xff.split(",") if p.strip()]):
        if raw not in _TRUSTED_PROXY_IPS:
            return raw
    return tcp_peer


# Default global throttle for API endpoints; individual routes can override.
limiter = Limiter(key_func=_rate_limit_key, default_limits=["100/minute"])
