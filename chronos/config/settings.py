from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenMetadata
    openmetadata_host: str = "http://localhost:8585"
    openmetadata_jwt_token: str = ""

    # Graphiti / FalkorDB
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    graphiti_mcp_url: str = "http://localhost:8200/mcp/"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    litellm_master_key: str = "sk-chronos-local"
    litellm_proxy_url: str = "http://localhost:4000"

    # Slack
    slack_webhook_url: str = ""
    slack_channel: str = "#data-incidents"

    # Langfuse
    langfuse_enabled: bool = True
    langfuse_host: str = "http://localhost:3002"
    langfuse_public_key: str = "pk-lf-chronos-demo"
    langfuse_secret_key: str = "sk-lf-chronos-demo"

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "chronos"

    # Application
    version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False
    investigation_window_hours: int = 72
    investigation_dedup_window_seconds: int = 300
    lineage_upstream_depth: int = 5
    lineage_downstream_depth: int = 3
    log_level: str = "INFO"


settings = Settings()
