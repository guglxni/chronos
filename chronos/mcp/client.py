"""
Unified async MCP client for CHRONOS.

Maintains persistent httpx sessions for HTTP-based MCP servers and dispatches
JSON-RPC 2.0 tool calls to the correct server by MCPServerType.

Fix #1: openmetadata_jwt_token is now SecretStr; unwrapped via secret_or_none().
Fix #4: broad ``except Exception`` replaced with httpx.HTTPStatusError,
        httpx.RequestError, and json.JSONDecodeError — each logged distinctly.
Fix #5: inline ``import json as _json`` moved to module-level.
"""

from __future__ import annotations

import itertools
import json
import logging
from typing import Any

import httpx

from chronos.config.settings import secret_or_none, settings
from chronos.mcp.config import MCPServerConfig, MCPServerType, get_mcp_configs

logger = logging.getLogger("chronos.mcp")

_TIMEOUT = 30.0
_rpc_counter = itertools.count(1)


def _next_rpc_id() -> int:
    return next(_rpc_counter)


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
            jwt_token = secret_or_none(settings.openmetadata_jwt_token)
            if server_type == MCPServerType.OPENMETADATA and jwt_token:
                headers["Authorization"] = f"Bearer {jwt_token}"
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
        Each error type is logged with its exception class name for triage.
        """
        session = self._get_session(server)
        if session is None:
            logger.warning("No HTTP session for server %s — tool call skipped", server)
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
                "MCP HTTP error [%s/%s]: %d %s",
                server,
                tool_name,
                exc.response.status_code,
                exc.response.text[:200],
            )
            return {}
        except httpx.RequestError as exc:
            logger.error(
                "MCP transport error [%s/%s]: %r", server, tool_name, exc
            )
            return {}
        except json.JSONDecodeError as exc:
            logger.error(
                "MCP malformed JSON [%s/%s]: %s", server, tool_name, exc
            )
            return {}

        # Unwrap JSON-RPC response
        if "error" in data:
            err = data["error"]
            logger.error("MCP RPC error [%s/%s]: %s", server, tool_name, err)
            return {}

        result = data.get("result", {})

        # MCP spec: result may be {"content": [...]} with text items
        if isinstance(result, dict) and "content" in result:
            content_items = result["content"]
            if isinstance(content_items, list) and content_items:
                first = content_items[0]
                if isinstance(first, dict) and first.get("type") == "text":
                    raw_text = first.get("text", "")
                    try:
                        parsed = json.loads(raw_text)
                        if isinstance(parsed, dict):
                            return parsed
                        return {"value": parsed}
                    except (json.JSONDecodeError, TypeError):
                        return {"text": raw_text}

        if isinstance(result, dict):
            return {str(key): value for key, value in result.items()}
        return {"value": result}

    async def close(self) -> None:
        """Close all open HTTP sessions."""
        for session in self._sessions.values():
            await session.aclose()
        self._sessions.clear()

    async def __aenter__(self) -> MCPClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()


# Module-level singleton
mcp_client = MCPClient()
