"""
A2A Agent Card endpoint for agent discovery (Linux Foundation A2A Protocol).

Exposes a machine-readable descriptor of CHRONOS's capabilities, skills,
and API contract at the well-known path /.well-known/agent-card.json.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from chronos.config.settings import settings

router = APIRouter(tags=["discovery"])


@router.get("/.well-known/agent-card.json")
async def get_agent_card():
    """Return the CHRONOS A2A Agent Card."""
    card = {
        "schemaVersion": "1.0",
        "name": "CHRONOS",
        "description": (
            "Autonomous Data Incident Root Cause Analysis Agent. "
            "Investigates data quality test failures by reasoning across "
            "OpenMetadata, Graphiti temporal knowledge graph, and GitNexus code graph."
        ),
        "version": settings.version,
        "homepage": "https://github.com/chronos-data/chronos",
        "provider": {
            "name": "CHRONOS",
            "url": "http://localhost:8100",
        },
        "authentication": {
            "type": "none",
            "description": "Internal use only — no auth required for local deployment",
        },
        "skills": [
            {
                "id": "investigate",
                "name": "Investigate Data Incident",
                "description": (
                    "Given an entity FQN and test name, runs a full 10-step RCA "
                    "investigation and returns a structured incident report with "
                    "confidence scoring."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_fqn": {
                            "type": "string",
                            "description": "Fully qualified name of the affected entity",
                        },
                        "test_name": {
                            "type": "string",
                            "description": "Name of the failing test case",
                        },
                        "failure_message": {"type": "string"},
                    },
                    "required": ["entity_fqn"],
                },
                "outputSchema": {
                    "type": "object",
                    "description": (
                        "IncidentReport with root_cause_category, confidence, "
                        "evidence_chain, recommended_actions"
                    ),
                },
            },
            {
                "id": "blast_radius_assessment",
                "name": "Blast Radius Assessment",
                "description": (
                    "Given an entity FQN, walks downstream lineage to identify "
                    "all affected assets and owners."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_fqn": {"type": "string"},
                        "depth": {"type": "integer", "default": 3},
                    },
                    "required": ["entity_fqn"],
                },
            },
            {
                "id": "compliance_report_generation",
                "name": "Compliance Report Generation",
                "description": (
                    "Generates W3C PROV-O provenance artifacts "
                    "(JSON-LD, Turtle, PROV-N) for a given incident investigation."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "incident_id": {"type": "string"},
                        "format": {
                            "type": "string",
                            "enum": ["jsonld", "ttl", "provn"],
                        },
                    },
                    "required": ["incident_id"],
                },
            },
        ],
        "capabilities": {
            "streaming": True,
            "asyncInvocation": True,
            "provenance": True,
            "protocols": ["HTTP", "SSE"],
        },
        "endpoints": {
            "investigate": "POST /api/v1/investigate",
            "incidents": "GET /api/v1/incidents",
            "stream": "GET /api/v1/investigations/{incident_id}/stream",
            "provenance": "GET /api/v1/incidents/{incident_id}/provenance.{format}",
            "health": "GET /api/v1/health",
            "agent_card": "GET /.well-known/agent-card.json",
        },
    }
    return JSONResponse(content=card)
