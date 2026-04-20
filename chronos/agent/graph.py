"""
LangGraph investigation state machine.

Wires all 10 nodes in a linear pipeline and exposes a compiled graph plus a
helper to create a Langfuse callback for each investigation run.
"""

from __future__ import annotations

import logging

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
from chronos.config.settings import settings

logger = logging.getLogger("chronos.agent.graph")


def build_investigation_graph() -> StateGraph:
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


def get_langfuse_callback(incident_id: str):
    """
    Return a LangfuseCallbackHandler for the given investigation, or None if
    Langfuse is disabled or the package is unavailable.
    """
    if not settings.langfuse_enabled:
        return None

    try:
        from langfuse.callback import CallbackHandler as LangfuseCallback  # type: ignore

        return LangfuseCallback(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            session_id=incident_id,
            trace_name=f"chronos-investigation-{incident_id}",
        )
    except ImportError:
        logger.warning("langfuse not installed — Langfuse tracing disabled")
        return None
    except Exception as exc:
        logger.warning(f"Failed to create Langfuse callback: {exc}")
        return None


# Module-level compiled graph (instantiated once at import time)
investigation_graph = build_investigation_graph()
