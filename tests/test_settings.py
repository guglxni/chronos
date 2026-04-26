"""
Unit tests for chronos.config.settings.Settings model_validator.

All tests construct Settings directly with kwargs so that the validator runs
in-process without reading any .env file or environment variables.
"""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from chronos.config.settings import Settings


def _dev(**overrides) -> Settings:
    """Create a minimal valid development Settings without loading .env."""
    base = dict(environment="development")
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


def _prod(**overrides) -> Settings:
    """Create a minimal valid production Settings without loading .env."""
    base = dict(
        environment="production",
        webhook_hmac_secret=SecretStr("super-secret-32-chars-exactly!!"),
        litellm_master_key=SecretStr("master"),
        openmetadata_jwt_token=SecretStr("jwt-token"),
        anthropic_api_key=SecretStr("sk-ant-test"),
        openmetadata_host="https://om.example.com",
        litellm_proxy_url="https://llm.example.com",
        graphiti_mcp_url="https://graphiti.example.com/sse",
        langfuse_host="https://langfuse.example.com",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


# ── development mode ──────────────────────────────────────────────────────────


def test_dev_allows_http_urls():
    s = _dev(openmetadata_host="http://localhost:8585")
    assert s.openmetadata_host.startswith("http://")


def test_dev_webhook_signing_off_by_default():
    s = _dev()
    assert s.webhook_signature_required is False


def test_dev_optional_secrets_absent_is_fine():
    s = _dev()
    assert s.litellm_master_key is None


# ── production mode ───────────────────────────────────────────────────────────


def test_prod_valid_config_passes():
    s = _prod()
    assert s.environment == "production"


def test_prod_forces_webhook_signing():
    """Production should always require signed webhooks, regardless of the raw field.

    The field itself stays at its default (False) — we expose an
    ``effective_webhook_signature_required`` property that OR's the production
    flag, so callers always check the property rather than the raw field.
    """
    s = _prod()
    assert s.effective_webhook_signature_required is True


def test_prod_rejects_http_openmetadata():
    with pytest.raises(ValueError, match="https://"):
        _prod(openmetadata_host="http://insecure.example.com")


def test_prod_rejects_http_litellm():
    with pytest.raises(ValueError, match="https://"):
        _prod(litellm_proxy_url="http://insecure.example.com")


def test_prod_rejects_http_graphiti():
    with pytest.raises(ValueError, match="https://"):
        _prod(graphiti_mcp_url="http://insecure.example.com/sse")


def test_prod_rejects_http_langfuse():
    with pytest.raises(ValueError, match="https://"):
        _prod(langfuse_host="http://langfuse.internal.example.com")


def test_prod_missing_litellm_master_key_raises():
    with pytest.raises(ValueError, match="LITELLM_MASTER_KEY"):
        _prod(litellm_master_key=None)


def test_prod_missing_webhook_secret_raises():
    with pytest.raises(ValueError, match="WEBHOOK_HMAC_SECRET"):
        _prod(webhook_hmac_secret=None)


def test_prod_missing_openmetadata_token_raises():
    with pytest.raises(ValueError, match="OPENMETADATA_JWT_TOKEN"):
        _prod(openmetadata_jwt_token=None)


# ── webhook signing in non-production ─────────────────────────────────────────


def test_dev_webhook_signing_enabled_requires_secret():
    with pytest.raises(ValueError, match="WEBHOOK_HMAC_SECRET"):
        _dev(webhook_signature_required=True, webhook_hmac_secret=None)


def test_dev_webhook_signing_with_secret_passes():
    s = _dev(
        webhook_signature_required=True,
        webhook_hmac_secret=SecretStr("a-strong-secret-here"),
    )
    assert s.webhook_signature_required is True


# ── langfuse feature flag ─────────────────────────────────────────────────────


def test_langfuse_enabled_requires_keys():
    with pytest.raises(ValueError, match="LANGFUSE"):
        _dev(langfuse_enabled=True)


def test_langfuse_disabled_without_keys_passes():
    s = _dev(langfuse_enabled=False)
    assert s.langfuse_enabled is False


# ── production LLM key requirement (B2) ──────────────────────────────────────


def test_prod_requires_at_least_one_llm_key():
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        _prod(anthropic_api_key=None, openai_api_key=None, groq_api_key=None)


def test_prod_openai_key_satisfies_llm_requirement():
    s = _prod(anthropic_api_key=None, openai_api_key=SecretStr("sk-openai"))
    assert s.openai_api_key is not None


def test_prod_groq_key_satisfies_llm_requirement():
    s = _prod(anthropic_api_key=None, groq_api_key=SecretStr("gsk-groq"))
    assert s.groq_api_key is not None


# ── cors_origins helper ───────────────────────────────────────────────────────


def test_cors_origins_splits_comma_separated():
    s = _dev(cors_allowed_origins="http://localhost:3000,http://localhost:5173")
    assert len(s.cors_origins) == 2
    assert "http://localhost:3000" in s.cors_origins


def test_cors_origins_trims_whitespace():
    s = _dev(cors_allowed_origins="http://a.com , http://b.com")
    assert all("  " not in o for o in s.cors_origins)
