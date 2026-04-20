"""
LiteLLM proxy client for RCA synthesis and structured extraction.

Uses httpx to call the LiteLLM proxy REST API directly — this avoids any SDK
version coupling and works with the proxy's model aliasing/fallback routing.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from chronos.config.settings import settings
from chronos.llm.prompts import (
    EXTRACTION_PROMPT,
    RCA_SYSTEM_PROMPT,
    RCA_USER_TEMPLATE,
)

logger = logging.getLogger("chronos.llm")

_CHAT_ENDPOINT = "/chat/completions"
_TIMEOUT = 120.0  # seconds — RCA synthesis can take a moment


def _litellm_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json",
    }


async def _call_litellm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """
    POST to LiteLLM proxy /chat/completions and return the assistant message content.
    Raises on non-2xx or malformed responses.
    """
    url = settings.litellm_proxy_url.rstrip("/") + _CHAT_ENDPOINT
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(url, headers=_litellm_headers(), json=payload)
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"LiteLLM returned no choices: {data}")

    content: str = choices[0].get("message", {}).get("content", "")
    return content


def _parse_json_response(raw: str) -> dict[str, Any]:
    """
    Attempt to parse JSON from a raw LLM response.
    Handles markdown code fences (```json ... ```) gracefully.
    """
    raw = raw.strip()

    # Strip optional markdown code fence
    if raw.startswith("```"):
        lines = raw.splitlines()
        # Drop first line (``` or ```json) and last line (```)
        inner_lines = []
        for line in lines[1:]:
            if line.strip() == "```":
                break
            inner_lines.append(line)
        raw = "\n".join(inner_lines).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse LLM JSON response: {exc}\nRaw:\n{raw[:500]}")
        return {}


async def synthesize_rca(evidence: dict[str, Any]) -> dict[str, Any]:
    """
    Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause
    analysis from the collected evidence dict.

    Returns a dict matching the RCA JSON schema, or an empty/partial dict on failure.
    """
    user_message = RCA_USER_TEMPLATE.format(
        failed_test=json.dumps(evidence.get("failed_test", {}), indent=2, default=str),
        affected_entity=json.dumps(evidence.get("affected_entity", {}), indent=2, default=str),
        temporal_changes=json.dumps(evidence.get("temporal_changes", []), indent=2, default=str),
        schema_changes=json.dumps(evidence.get("schema_changes", []), indent=2, default=str),
        upstream_lineage=json.dumps(evidence.get("upstream_failures", []), indent=2, default=str),
        code_changes=json.dumps(evidence.get("related_code_files", []), indent=2, default=str),
        downstream_impact=json.dumps(evidence.get("downstream_assets", []), indent=2, default=str),
        audit_events=json.dumps(evidence.get("audit_events", []), indent=2, default=str),
        prior_incidents=json.dumps(evidence.get("prior_investigations", []), indent=2, default=str),
        business_impact_score=evidence.get("business_impact_score", "medium"),
        window_hours=str(settings.investigation_window_hours),
    )

    messages = [
        {"role": "system", "content": RCA_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await _call_litellm(
            model="chronos-synthesis",
            messages=messages,
            temperature=0.1,
            max_tokens=2048,
        )
        result = _parse_json_response(raw)
        logger.info(
            f"RCA synthesis complete: category={result.get('root_cause_category')}, "
            f"confidence={result.get('confidence')}"
        )
        return result
    except Exception as exc:
        logger.error(f"RCA synthesis failed: {exc}", exc_info=True)
        return {
            "probable_root_cause": "Investigation incomplete — LLM synthesis failed.",
            "root_cause_category": "UNKNOWN",
            "confidence": 0.0,
            "evidence_chain": [],
            "business_impact": evidence.get("business_impact_score", "medium"),
            "recommended_actions": [
                {
                    "description": "Manually review evidence and re-trigger investigation.",
                    "priority": "immediate",
                    "owner": "data-engineering",
                }
            ],
        }


async def extract_structured(raw_text: str, schema_hint: str) -> dict[str, Any]:
    """
    Call LiteLLM proxy (chronos-extraction model — fast Groq model) to extract
    structured data from a raw MCP tool response.

    Returns parsed dict, or empty dict on failure.
    """
    prompt = EXTRACTION_PROMPT.format(schema_hint=schema_hint, raw_text=raw_text[:4000])
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = await _call_litellm(
            model="chronos-extraction",
            messages=messages,
            temperature=0.0,
            max_tokens=1024,
        )
        return _parse_json_response(raw)
    except Exception as exc:
        logger.error(f"Structured extraction failed: {exc}", exc_info=True)
        return {}
