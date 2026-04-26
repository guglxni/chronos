"""
LangGraph investigation state machine.

Wires all 10 nodes in a linear pipeline and exposes a compiled graph plus a
helper to create a Langfuse callback for each investigation run.

Fix #1: Langfuse public/secret keys are SecretStr; unwrapped via secret_or_none().
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from chronos.agent.nodes.audit_correlation import audit_correlation_node
from chronos.agent.nodes.code_blast_radius import code_blast_radius_node
from chronos.agent.nodes.downstream_impact import downstream_impact_node
from chronos.agent.nodes.lineage_walk import lineage_walk_node
from chronos.agent.nodes.notify import notify_node
from chronos.agent.nodes.persist_trace import persist_trace_node
from chronos.agent.nodes.prior_investigations import prior_investigations_node
from chronos.agent.nodes.rca_synthesis import rca_synthesis_node
from chronos.agent.nodes.scope_failure import scope_failure_node
from chronos.agent.nodes.temporal_diff import temporal_diff_node
from chronos.agent.state import InvestigationState
from chronos.config.settings import secret_or_none, settings

logger = logging.getLogger("chronos.agent.graph")

LangfuseCallback: Any = None

try:
    from langfuse.callback import CallbackHandler as _LangfuseCallback

    LangfuseCallback = _LangfuseCallback
except ImportError:
    pass

_investigation_graph_cache: Any = None


def build_investigation_graph() -> Any:
    """Construct and compile the 10-step investigation graph."""
    graph = StateGraph(InvestigationState)

    # Register nodes
    graph.add_node("step_0_prior", prior_investigations_node)
    graph.add_node("step_1_scope", scope_failure_node)
    graph.add_node("step_2_temporal", temporal_diff_node)
    graph.add_node("step_3_lineage", lineage_walk_node)
    graph.add_node("step_4_code", code_blast_radius_node)
    graph.add_node("step_5_downstream", downstream_impact_node)
    graph.add_node("step_6_audit", audit_correlation_node)
    graph.add_node("step_7_synthesis", rca_synthesis_node)
    graph.add_node("step_8_notify", notify_node)
    graph.add_node("step_9_persist", persist_trace_node)

    # Set entry point
    graph.set_entry_point("step_0_prior")

    # Wire linear pipeline
    graph.add_edge("step_0_prior", "step_1_scope")
    graph.add_edge("step_1_scope", "step_2_temporal")
    graph.add_edge("step_2_temporal", "step_3_lineage")
    graph.add_edge("step_3_lineage", "step_4_code")
    graph.add_edge("step_4_code", "step_5_downstream")
    graph.add_edge("step_5_downstream", "step_6_audit")
    graph.add_edge("step_6_audit", "step_7_synthesis")
    graph.add_edge("step_7_synthesis", "step_8_notify")
    graph.add_edge("step_8_notify", "step_9_persist")
    graph.add_edge("step_9_persist", END)

    return graph.compile()


def get_investigation_graph() -> Any:
    """Return a lazily-compiled investigation graph instance."""
    global _investigation_graph_cache
    if _investigation_graph_cache is None:
        _investigation_graph_cache = build_investigation_graph()
    return _investigation_graph_cache


def get_langfuse_callback(incident_id: str) -> Any:
    """
    Return a LangfuseCallbackHandler for the given investigation, or None if
    Langfuse is disabled or the package is unavailable.
    """
    if not settings.langfuse_enabled:
        return None

    public_key = secret_or_none(settings.langfuse_public_key)
    secret_key = secret_or_none(settings.langfuse_secret_key)
    if not public_key or not secret_key:
        logger.warning(
            "Langfuse keys not configured — tracing disabled for incident %s", incident_id
        )
        return None

    if LangfuseCallback is None:
        logger.warning("langfuse package not installed — tracing disabled")
        return None

    try:
        return LangfuseCallback(
            public_key=public_key,
            secret_key=secret_key,
            host=settings.langfuse_host,
            session_id=incident_id,
            trace_name=f"chronos-investigation-{incident_id}",
        )
    except (ValueError, RuntimeError) as exc:
        logger.warning("Failed to create Langfuse callback: %s", exc)
        return None
