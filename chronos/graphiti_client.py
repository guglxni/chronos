"""
In-process Graphiti client.

Replaces the graphiti-mcp sidecar with direct graphiti-core calls so that
Heroku deployments (which don't run the MCP server) can still persist and
query the knowledge graph when a real FalkorDB is configured.

When ``_is_configured()`` returns False (localhost / default dev values),
all public functions return empty results immediately — no connection attempt,
no exception.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import numpy as np

from chronos.config.settings import secret_or_none, settings

if TYPE_CHECKING:
    from graphiti_core import Graphiti

logger = logging.getLogger("chronos.graphiti_client")

# Hosts that indicate "not configured for real Graphiti usage"
_LOCAL_HOSTS: frozenset[str] = frozenset({"localhost", "falkordb", "127.0.0.1"})

_graphiti_instance: Graphiti | None = None

_EMBED_DIM = 1024


# ─── Deterministic hash embedder ──────────────────────────────────────────────


class _HashEmbedder:
    """Deterministic SHA-256-seeded unit-vector embedder — no external API."""

    class config:  # matches EmbedderClient.config protocol
        embedding_dim: int = _EMBED_DIM

    async def create(self, input_data: Any) -> list[float]:
        text = input_data if isinstance(input_data, str) else str(input_data)
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(_EMBED_DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()  # type: ignore[no-any-return]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        return [await self.create(text) for text in input_data_list]


# ─── Configuration guard ──────────────────────────────────────────────────────


def _is_configured() -> bool:
    """Return True only when a non-local FalkorDB host is set."""
    return settings.falkordb_host not in _LOCAL_HOSTS


# ─── Lazy singleton ───────────────────────────────────────────────────────────


async def _get_graphiti() -> Graphiti | None:
    global _graphiti_instance

    if _graphiti_instance is not None:
        return _graphiti_instance

    try:
        from graphiti_core import Graphiti
        from graphiti_core.driver.falkordb_driver import FalkorDBDriver
        from graphiti_core.llm_client.config import LLMConfig
        from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
        from openai import AsyncOpenAI
    except ImportError as exc:
        logger.warning("graphiti_client: missing dependency, graphiti disabled: %s", exc)
        return None

    password = secret_or_none(settings.falkordb_password)
    driver = FalkorDBDriver(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        password=password,
    )

    api_key = secret_or_none(settings.litellm_master_key) or "placeholder"
    openai_client = AsyncOpenAI(
        base_url=settings.litellm_proxy_url,
        api_key=api_key,
    )
    llm_client = OpenAIGenericClient(
        config=LLMConfig(model=settings.llm_model),
        client=openai_client,
    )

    instance = Graphiti(
        graph_driver=driver,
        llm_client=llm_client,
        embedder=_HashEmbedder(),  # type: ignore[arg-type]
    )

    try:
        await instance.build_indices_and_constraints()
    except Exception as exc:  # non-fatal — graph still usable without indices
        logger.warning("graphiti_client: build_indices_and_constraints failed: %s", exc)

    _graphiti_instance = instance
    return _graphiti_instance


# ─── Public API ───────────────────────────────────────────────────────────────


async def add_episode(
    group_id: str,
    name: str,
    content: str,
    source_type: str = "json",
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Add an episode to the knowledge graph.

    ``reference_time`` defaults to "now" but can be set to a past timestamp
    for backfilling historical episodes (e.g., the demo seeder).
    """
    if not _is_configured():
        logger.debug("graphiti_client: not configured, skipping add_episode")
        return {}

    try:
        from graphiti_core.nodes import EpisodeType

        g = await _get_graphiti()
        if g is None:
            return {}

        ep_type = (
            EpisodeType[source_type] if source_type in EpisodeType.__members__ else EpisodeType.text
        )
        await g.add_episode(
            name=name,
            episode_body=content,
            source=ep_type,
            source_description="chronos",
            reference_time=reference_time if reference_time is not None else datetime.now(UTC),
            group_id=group_id,
        )
        return {"status": "ok", "group_id": group_id, "name": name}
    except Exception as exc:
        logger.warning("graphiti_client.add_episode failed: %s", exc)
        return {}


async def search_facts(
    query: str,
    group_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search for facts (edges) in a Graphiti group."""
    if not _is_configured():
        logger.debug("graphiti_client: not configured, skipping search_facts")
        return []

    try:
        g = await _get_graphiti()
        if g is None:
            return []

        edges = await g.search(
            query=query,
            group_ids=[group_id],
            num_results=limit,
        )
        return [
            {
                "uuid": str(e.uuid),
                "name": e.name,
                "fact": e.fact,
                "source_node_uuid": str(e.source_node_uuid),
                "target_node_uuid": str(e.target_node_uuid),
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in edges
        ]
    except Exception as exc:
        logger.warning("graphiti_client.search_facts failed: %s", exc)
        return []


async def search_nodes(
    query: str,
    group_id: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Search for entity nodes in a Graphiti group."""
    if not _is_configured():
        logger.debug("graphiti_client: not configured, skipping search_nodes")
        return []

    try:
        from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
        from graphiti_core.search.search_filters import SearchFilters

        g = await _get_graphiti()
        if g is None:
            return []

        results = await g.search_(  # type: ignore[call-arg]
            query=query,
            group_ids=[group_id],
            num_results=limit,
            search_config=NODE_HYBRID_SEARCH_RRF,
            search_filter=SearchFilters(),
        )
        nodes = getattr(results, "nodes", []) or []
        return [
            {
                "uuid": str(n.uuid),
                "name": n.name,
                "group_id": n.group_id,
                "summary": getattr(n, "summary", ""),
                "labels": list(getattr(n, "labels", [])),
            }
            for n in nodes
        ]
    except Exception as exc:
        logger.warning("graphiti_client.search_nodes failed: %s", exc)
        return []


async def get_episodes(
    group_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve the most recent episodes in a Graphiti group."""
    if not _is_configured():
        logger.debug("graphiti_client: not configured, skipping get_episodes")
        return []

    try:
        g = await _get_graphiti()
        if g is None:
            return []

        episodes = await g.retrieve_episodes(
            reference_time=datetime.now(UTC),
            last_n=limit,
            group_ids=[group_id],
        )
        return [
            {
                "uuid": str(ep.uuid),
                "name": ep.name,
                "group_id": ep.group_id,
                "content": ep.content,
                "source": ep.source.value if ep.source else None,
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
            }
            for ep in episodes
        ]
    except Exception as exc:
        logger.warning("graphiti_client.get_episodes failed: %s", exc)
        return []
