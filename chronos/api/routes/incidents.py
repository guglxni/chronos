"""
Incident CRUD REST API and W3C PROV-O provenance export endpoints.

The in-memory incident store has been extracted to ``chronos/core/incident_store.py``
so that the investigation runner can persist reports without importing from the
API layer (Fix #5 — circular import elimination).

This module is now a thin HTTP adapter: it maps HTTP requests to typed
``IncidentReport`` operations and serialises responses at the JSON boundary
via ``model_dump(mode="json")``.  All field access uses attribute access on
the typed model — no dict.get() on required fields (Fix #3).
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from chronos.api.dependencies import verify_bearer_token
from chronos.api.schemas import AcknowledgeResponse, IncidentListResponse, ResolveResponse
from chronos.compliance.prov_generator import safe_generate_provenance as generate_provenance
from chronos.core import incident_store
from chronos.models.incident import IncidentReport, IncidentStatus, RootCauseCategory

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])
logger = logging.getLogger("chronos.incidents")


# ── Public store helper (backward-compat shim for callers that used to import
# store_incident directly from this module) ────────────────────────────────────

def store_incident(incident_report: dict | IncidentReport) -> None:
    """
    Persist a completed incident report.

    Delegates to ``core.incident_store``; kept here so existing imports from
    this module continue to work without changes.
    """
    incident_store.store(incident_report)


# ── List & filter ──────────────────────────────────────────────────────────────

@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: str | None = None,
    root_cause: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List incidents with optional filtering by status and root cause category."""
    incidents = incident_store.list_all()

    # Validate enum values early so callers get a clear 400, not a silent empty list
    if status:
        try:
            status_enum = IncidentStatus(status)
        except ValueError as err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. "
                       f"Valid values: {[e.value for e in IncidentStatus]}",
            ) from err
        incidents = [i for i in incidents if i.status == status_enum]

    if root_cause:
        try:
            rc_enum = RootCauseCategory(root_cause)
        except ValueError as err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid root_cause '{root_cause}'. "
                       f"Valid values: {[e.value for e in RootCauseCategory]}",
            ) from err
        incidents = [i for i in incidents if i.root_cause_category == rc_enum]

    # Sort by detected_at descending (typed attribute — no .get() needed)
    incidents.sort(key=lambda x: x.detected_at, reverse=True)

    paginated = incidents[offset : offset + limit]
    return {
        "total": len(incidents),
        "limit": limit,
        "offset": offset,
        "incidents": [i.model_dump(mode="json") for i in paginated],
    }


# ── Single incident ────────────────────────────────────────────────────────────

@router.get("/{incident_id}", response_model=IncidentReport)
async def get_incident(incident_id: str) -> dict[str, Any]:
    """Retrieve a specific incident by ID."""
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident.model_dump(mode="json")


# ── Mutations ──────────────────────────────────────────────────────────────────

@router.post(
    "/{incident_id}/acknowledge",
    response_model=AcknowledgeResponse,
    dependencies=[Depends(verify_bearer_token)],
)
async def acknowledge_incident(incident_id: str, user: str = "anonymous") -> dict[str, Any]:
    """Acknowledge an incident — marks it as seen by a human."""
    try:
        updated = incident_store.update_field(
            incident_id,
            status=IncidentStatus.ACKNOWLEDGED,
            acknowledged_by=user,
        )
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found",
        ) from err
    logger.info("Incident %s acknowledged by %s", incident_id, user)
    return {
        "status": "acknowledged",
        "incident_id": updated.incident_id,
        "acknowledged_by": updated.acknowledged_by,
    }


@router.post(
    "/{incident_id}/resolve",
    response_model=ResolveResponse,
    dependencies=[Depends(verify_bearer_token)],
)
async def resolve_incident(incident_id: str, user: str = "anonymous") -> dict[str, Any]:
    """Resolve an incident."""
    try:
        updated = incident_store.update_field(
            incident_id,
            status=IncidentStatus.RESOLVED,
            resolved_by=user,
            resolved_at=datetime.now(tz=UTC),
        )
    except KeyError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found",
        ) from err
    logger.info("Incident %s resolved by %s", incident_id, user)
    return {
        "status": "resolved",
        "incident_id": updated.incident_id,
        "resolved_by": updated.resolved_by,
        "resolved_at": updated.resolved_at.isoformat() if updated.resolved_at else None,
    }


# ── W3C PROV-O Provenance endpoints ──────────────────────────────────────────

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _get_incident_or_404(incident_id: str) -> IncidentReport:
    """Return typed incident or raise HTTP 404.

    Also validates that incident_id contains only safe characters so it
    cannot inject newlines into Content-Disposition headers.
    """
    if not _SAFE_ID_RE.match(incident_id):
        raise HTTPException(status_code=400, detail="Invalid incident ID format")
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.get("/{incident_id}/provenance.jsonld")
async def get_provenance_jsonld(incident_id: str) -> Response:
    """Download W3C PROV-O provenance document as JSON-LD."""
    incident = _get_incident_or_404(incident_id)
    prov_doc = generate_provenance(incident.model_dump(mode="json"))
    jsonld_bytes = prov_doc.serialize(format="json")
    return Response(
        content=jsonld_bytes,
        media_type="application/ld+json",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.jsonld"'
        },
    )


@router.get("/{incident_id}/provenance.ttl")
async def get_provenance_turtle(incident_id: str) -> Response:
    """Download W3C PROV-O provenance document as Turtle RDF."""
    incident = _get_incident_or_404(incident_id)
    prov_doc = generate_provenance(incident.model_dump(mode="json"))
    turtle_bytes = prov_doc.serialize(format="rdf", rdf_format="turtle")
    return Response(
        content=turtle_bytes,
        media_type="text/turtle",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.ttl"'
        },
    )


@router.get("/{incident_id}/provenance.provn")
async def get_provenance_provn(incident_id: str) -> Response:
    """Download W3C PROV-O provenance document as PROV-N notation."""
    incident = _get_incident_or_404(incident_id)
    prov_doc = generate_provenance(incident.model_dump(mode="json"))
    provn_str = prov_doc.serialize(format="provn")
    return Response(
        content=provn_str,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="provenance-{incident_id}.provn"'
        },
    )
