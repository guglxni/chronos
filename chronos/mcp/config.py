from dataclasses import dataclass, field
from enum import StrEnum

from chronos.config.settings import settings


class MCPServerType(StrEnum):
    OPENMETADATA = "openmetadata"
    GRAPHITI = "graphiti"
    GITNEXUS = "gitnexus"
    GRAPHIFY = "graphify"


@dataclass
class MCPServerConfig:
    name: str
    server_type: MCPServerType
    url: str | None = None
    command: str | None = None
    args: list[str] | None = field(default=None)


def get_mcp_configs() -> dict[str, MCPServerConfig]:
    return {
        MCPServerType.OPENMETADATA: MCPServerConfig(
            name="openmetadata",
            server_type=MCPServerType.OPENMETADATA,
            url=f"{settings.openmetadata_host}/api/v1/mcp",
        ),
        MCPServerType.GRAPHITI: MCPServerConfig(
            name="graphiti",
            server_type=MCPServerType.GRAPHITI,
            url=settings.graphiti_mcp_url,
        ),
        # GitNexus: kept for backwards compatibility. The actual implementation
        # falls back to the in-process ``chronos.code_intel`` backend when
        # ``settings.code_intel_prefer_local`` is True or the binary is absent
        # (the upstream GitNexus is browser-only / non-commercial — see
        # docs/code_intel_design.md). The ``command`` here matches the
        # historical contract so nothing breaks if you do wire a real CLI.
        MCPServerType.GITNEXUS: MCPServerConfig(
            name="gitnexus",
            server_type=MCPServerType.GITNEXUS,
            command="gitnexus",
            args=["serve", "--stdio"],
        ),
        # Graphify: in-process by default (the adapter loads graph.json
        # directly via NetworkX). The optional CLI form ``graphify --mcp``
        # is recorded for future remote-server deployments.
        MCPServerType.GRAPHIFY: MCPServerConfig(
            name="graphify",
            server_type=MCPServerType.GRAPHIFY,
            command="graphify",
            args=["--mcp", settings.graphify_graph_path],
        ),
    }
