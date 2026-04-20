from dataclasses import dataclass, field
from enum import Enum

from chronos.config.settings import settings


class MCPServerType(str, Enum):
    OPENMETADATA = "openmetadata"
    GRAPHITI = "graphiti"
    GITNEXUS = "gitnexus"


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
        MCPServerType.GITNEXUS: MCPServerConfig(
            name="gitnexus",
            server_type=MCPServerType.GITNEXUS,
            command="gitnexus",
            args=["serve", "--stdio"],
        ),
    }
