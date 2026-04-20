"""
Incident CRUD REST API and W3C PROV-O provenance export endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from chronos.models.incident import IncidentStatus

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])
logger = logging.getLogger("chronos.incidents")

# In-memory incident store.
# In production this would be backed by a database (PostgreSQL, DynamoDB, etc.).
_incidents: dict[str, dict] = {}


def store_incident(incident_report: dict) -> None:
    """Store a completed incident report (called by the investigation pipeline)."""
    incident_id = incident_report.get("incident_id", "")
    if incident_id:
        _incidents[incident_id] = incident_report
        logger.info(f"Stored incident {incident_id}")


@router.get("")
async def list_incidents(
    status: str | None = None,
    root_cause: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List incidents with optional filtering by status and root cause category."""
    incidents = list(_incidents.values())

    if status:
        incidents = [i for i in incidents if i.get("status") == status]
    if root_cause:
        incidents = [
            i for i in incidents if i.get("root_cause_category") == root_cause
        ]

    # Sort by detected_at descending (most recent first)
    incidents.sort(key=lambda x: x.get("detected_at", ""), reverse=True)

    paginated = incidents[offset : offset + limit]
    return {"total": len(incidents), "limit": limit, "offset": offset, "incidents": paginated}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Retrieve a specific incident by ID."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.post("/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str, user: str = "anonymous"):
    """Acknowledge an incident — marks it as seen by a human."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    incident["status"] = IncidentStatus.ACKNOWLEDGED.value
    incident["acknowledged_by"] = user
    logger.info(f"Incident {incident_id} acknowledged by {user}")
    return {"status": "acknowledged", "incident_id": incident_id, "acknowledged_by": user}


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, user: str = "anonymous"):
    """Resolve an incident."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    incident["status"] = IncidentStatus.RESOLVED.value
    incident["resolved_by"] = user
    incident["resolved_at"] = datetime.utcnow().isoformat()
    logger.info(f"Incident {incident_id} resolved by {user}")
    return {
        "status": "resolved",
        "incident_id": incident_id,
        "resolved_by": user,
        "resolved_at": incident["resolved_at"],
    }


# ─── PROV-O Provenance endpoints ──────────────────────────────────────────────

def _get_incident_or_404(incident_id: str) -> dict:
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.get("/{incident_id}/provenance.jsonld")
async def get_provenance_jsonld(incident_id: str):
    """Download W3C PROV-O provenance document as JSON-LD."""
    incident = _get_incident_or_404(incident_id)
    from chronos.compliance.prov_generator import generate_provenance

    prov_doc = generate_provenance(incident)
    jsonld_bytes = prov_doc.serialize(format="json")
    return Response(
        content=jsonld_bytes,
        media_type="application/ld+json",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.jsonld"'
        },
    )


@router.get("/{incident_id}/provenance.ttl")
async def get_provenance_turtle(incident_id: str):
    """Download W3C PROV-O provenance document as Turtle RDF."""
    incident = _get_incident_or_404(incident_id)
    from chronos.compliance.prov_generator import generate_provenance

    prov_doc = generate_provenance(incident)
    turtle_bytes = prov_doc.serialize(format="rdf", rdf_format="turtle")
    return Response(
        content=turtle_bytes,
        media_type="text/turtle",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.ttl"'
        },
    )


@router.get("/{incident_id}/provenance.provn")
async def get_provenance_provn(incident_id: str):
    """Download W3C PROV-O provenance document as PROV-N notation."""
    incident = _get_incident_or_404(incident_id)
    from chronos.compliance.prov_generator import generate_provenance

    prov_doc = generate_provenance(incident)
    provn_str = prov_doc.serialize(format="provn")
    return Response(
        content=provn_str,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.provn"'
        },
    )
