"""
CHRONOS application settings.

All secrets are typed as ``SecretStr | None`` so that Pydantic's repr never
leaks their values into logs.  Callers must unwrap them via
``secret_or_none(settings.<field>)`` or ``.get_secret_value()``.

Environment-aware validation runs at startup via a model_validator so that
misconfigured deployments fail fast with a clear error listing every missing
required secret — not buried inside a request handler.
"""
from __future__ import annotations

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── Non-secret URLs / hostnames ───────────────────────────────────────────
    openmetadata_host: str = "http://localhost:8585"
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    # Upstream getzep/graphiti mcp_server serves SSE at /sse, not /mcp/.
    graphiti_mcp_url: str = "http://localhost:8200/sse"
    litellm_proxy_url: str = "http://localhost:4000"
    langfuse_host: str = "http://localhost:3002"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "chronos"

    # ─── Secrets (never emit values in logs; Pydantic redacts repr) ─────────────
    openmetadata_jwt_token: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    litellm_master_key: SecretStr | None = None
    slack_webhook_url: SecretStr | None = None
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None

    # ─── Webhook signing (Fix #2) ───────────────────────────────────────────────
    # In production set WEBHOOK_SIGNATURE_REQUIRED=true and supply a strong random
    # WEBHOOK_HMAC_SECRET.  In development both default to disabled/unset so that
    # manual webhook POSTs work without signing.
    webhook_hmac_secret: SecretStr | None = None
    webhook_signature_required: bool = False
    # Bearer token for mutation endpoints (acknowledge, resolve).
    # In dev: leave unset — auth check is skipped.
    # In prod: must be set; mutations are blocked if absent.
    api_bearer_token: SecretStr | None = None

    # ─── Service URLs (used for outbound links in Slack notifications etc.) ───────
    frontend_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8100"

    # ─── Feature flags ─────────────────────────────────────────────────────────
    langfuse_enabled: bool = False
    slack_channel: str = "#data-incidents"
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # ─── Application tuning ────────────────────────────────────────────────────
    version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False
    investigation_window_hours: int = 72
    investigation_dedup_window_seconds: int = 300
    investigation_timeout_seconds: int = 300
    lineage_upstream_depth: int = 5
    lineage_downstream_depth: int = 3
    log_level: str = "INFO"

    # ─── LLM model routing ─────────────────────────────────────────────────────
    # Model name passed to the LiteLLM proxy (or Groq/OpenAI-compat endpoint).
    # When using Groq directly (LITELLM_PROXY_URL=https://api.groq.com/openai/v1)
    # set this to the Groq model ID, e.g. meta-llama/llama-4-scout-17b-16e-instruct.
    llm_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # ─── Local code intelligence (replaces the GitNexus stub) ─────────────────
    # Path to the data-platform repo CHRONOS investigates (dbt project, ETL
    # code, etc.). Defaults to the current working directory so the in-tree
    # demo works without configuration.
    code_repo_path: str = "."
    # Path to the graphify-out artifact for live graph queries. Defaults to
    # the in-repo ``graphify-out/graph.json`` produced by ``graphify .``.
    graphify_graph_path: str = "graphify-out/graph.json"
    # Optional path to a dbt project's ``target/manifest.json`` for exact
    # lineage. Empty string disables the dbt backend.
    dbt_manifest_path: str = ""
    # Toggle to prefer the local backend over the (often-stubbed) GitNexus
    # MCP server. Default true — set false only if you wire a real GitNexus.
    code_intel_prefer_local: bool = True

    # ─── Startup validation ────────────────────────────────────────────────────
    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins as a trimmed list from a comma-separated string."""
        origins = [item.strip() for item in self.cors_allowed_origins.split(",")]
        return [item for item in origins if item]

    @model_validator(mode="after")
    def _validate_secrets_for_enabled_features(self) -> Settings:
        """
        Fail at startup — not deep in a request handler — when required secrets
        are absent for the features that are actually enabled.

        ``webhook_signature_required`` is exposed via the
        ``effective_webhook_signature_required`` property rather than back-mutating
        the field through ``object.__setattr__``.  The previous approach worked
        but bypassed Pydantic's validator contract and would break if BaseSettings
        ever gained ``frozen=True`` defaults.
        """
        missing: list[str] = []

        if self.langfuse_enabled:
            if self.langfuse_public_key is None:
                missing.append("LANGFUSE_PUBLIC_KEY")
            if self.langfuse_secret_key is None:
                missing.append("LANGFUSE_SECRET_KEY")

        if self.environment == "production":
            for field_name, value in (
                ("WEBHOOK_HMAC_SECRET", self.webhook_hmac_secret),
                ("LITELLM_MASTER_KEY", self.litellm_master_key),
                ("OPENMETADATA_JWT_TOKEN", self.openmetadata_jwt_token),
            ):
                if value is None:
                    missing.append(field_name)

            # Require at least one LLM provider key — a missing key causes every
            # investigation to silently produce a degraded result (LiteLLM returns
            # 401, RCA synthesis never runs), not a startup error.
            if not any(
                [self.anthropic_api_key, self.openai_api_key, self.groq_api_key]
            ):
                missing.append(
                    "at least one of ANTHROPIC_API_KEY / OPENAI_API_KEY / GROQ_API_KEY"
                )

            # Reject plain-HTTP URLs for external services in production — tokens
            # would travel in cleartext, violating data-handling policies.
            for url_field, url_value in (
                ("OPENMETADATA_HOST", self.openmetadata_host),
                ("LITELLM_PROXY_URL", self.litellm_proxy_url),
                ("GRAPHITI_MCP_URL", self.graphiti_mcp_url),
                ("LANGFUSE_HOST", self.langfuse_host),
            ):
                if url_value.startswith("http://"):
                    missing.append(
                        f"{url_field} (must use https:// in production, got: {url_value!r})"
                    )
        elif self.webhook_signature_required and self.webhook_hmac_secret is None:
            missing.append("WEBHOOK_HMAC_SECRET")

        # CORS wildcard + allow_credentials is a browser security violation.
        # FastAPI silently ignores credentials on wildcard origins but still
        # emits permissive headers that confuse clients.  Reject early.
        if "*" in self.cors_origins and len(self.cors_origins) == 1:
            missing.append(
                "CORS_ALLOWED_ORIGINS cannot be '*' — "
                "wildcard origin is incompatible with allow_credentials=True. "
                "Specify explicit origin URLs."
            )

        if missing:
            raise ValueError(
                f"Missing required secrets for enabled features: {', '.join(missing)}. "
                f"Set them in .env or as environment variables."
            )
        return self

    @property
    def effective_webhook_signature_required(self) -> bool:
        """Webhook signing is mandatory in production regardless of the field value.

        Production deployments cannot accidentally disable signing by leaving the
        flag ``False`` — this property is the source of truth callers should check.
        """
        return self.environment == "production" or self.webhook_signature_required


def secret_or_none(value: SecretStr | None) -> str | None:
    """
    Safely unwrap a SecretStr.  Returns None when the field is unset so callers
    can do a simple truthiness check before using the value.
    """
    return value.get_secret_value() if value is not None else None


settings = Settings()
