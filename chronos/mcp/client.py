"""
Unified async MCP client for CHRONOS.

Maintains persistent httpx sessions for HTTP-based MCP servers and dispatches
JSON-RPC 2.0 tool calls to the correct server by MCPServerType.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from chronos.config.settings import settings
from chronos.mcp.config import MCPServerConfig, MCPServerType, get_mcp_configs

logger = logging.getLogger("chronos.mcp")

_TIMEOUT = 30.0
_RPC_COUNTER = 0  # simple sequential ID; good enough for non-concurrent calls


def _next_rpc_id() -> int:
    global _RPC_COUNTER
    _RPC_COUNTER += 1
    return _RPC_COUNTER


class MCPClient:
    """
    Singleton async MCP client.

    Usage:
        result = await mcp_client.call_tool(MCPServerType.GRAPHITI, "search_facts", {...})
    """

    def __init__(self) -> None:
        self._configs: dict[str, MCPServerConfig] = get_mcp_configs()
        self._sessions: dict[str, httpx.AsyncClient] = {}

    def _get_session(self, server_type: MCPServerType) -> httpx.AsyncClient | None:
        """Return (or lazily create) a persistent httpx session for a server."""
        key = server_type.value
        if key not in self._sessions:
            cfg = self._configs.get(server_type)
            if cfg is None or cfg.url is None:
                return None  # Stdio-based server — handled separately
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if server_type == MCPServerType.OPENMETADATA and settings.openmetadata_jwt_token:
                headers["Authorization"] = f"Bearer {settings.openmetadata_jwt_token}"
            self._sessions[key] = httpx.AsyncClient(
                base_url=cfg.url,
                headers=headers,
                timeout=_TIMEOUT,
            )
        return self._sessions[key]

    async def call_tool(
        self,
        server: MCPServerType,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Call a named tool on the specified MCP server.

        Sends a JSON-RPC 2.0 ``tools/call`` request and extracts the result.
        Returns an empty dict on any error so callers can continue gracefully.
        """
        session = self._get_session(server)
        if session is None:
            logger.warning(f"No HTTP session for server {server} — tool call skipped")
            return {}

        rpc_payload = {
            "jsonrpc": "2.0",
            "id": _next_rpc_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        try:
            cfg = self._configs[server]
            url = cfg.url or ""
            response = await session.post(url, json=rpc_payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"MCP HTTP error [{server}/{tool_name}]: {exc.response.status_code} "
                f"{exc.response.text[:200]}"
            )
            return {}
        except Exception as exc:
            logger.error(f"MCP call failed [{server}/{tool_name}]: {exc}", exc_info=True)
            return {}

        # Unwrap JSON-RPC response
        if "error" in data:
            err = data["error"]
            logger.error(f"MCP RPC error [{server}/{tool_name}]: {err}")
            return {}

        result = data.get("result", {})

        # MCP spec: result may be {"content": [...]} with text items
        if isinstance(result, dict) and "content" in result:
            content_items = result["content"]
            if isinstance(content_items, list) and content_items:
                first = content_items[0]
                if isinstance(first, dict) and first.get("type") == "text":
                    import json as _json
                    raw_text = first.get("text", "")
                    try:
                        return _json.loads(raw_text)
                    except (_json.JSONDecodeError, TypeError):
                        return {"text": raw_text}

        return result if isinstance(result, dict) else {"value": result}

    async def close(self) -> None:
        """Close all open HTTP sessions."""
        for session in self._sessions.values():
            await session.aclose()
        self._sessions.clear()

    async def __aenter__(self) -> "MCPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()


# Module-level singleton
mcp_client = MCPClient()
