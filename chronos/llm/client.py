"""
LiteLLM proxy client for RCA synthesis and structured extraction.

Uses httpx to call the LiteLLM proxy REST API directly — this avoids any SDK
version coupling and works with the proxy's model aliasing/fallback routing.

Fix #1: litellm_master_key is now SecretStr; unwrapped via secret_or_none().
Fix #4: broad ``except Exception`` replaced with specific error types — network
        failures, timeouts, and JSON parse errors are caught distinctly so each
        failure mode produces a diagnostic log entry.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from chronos.config.settings import secret_or_none, settings
from chronos.llm.prompts import (
    EXTRACTION_PROMPT,
    RCA_SYSTEM_PROMPT,
    RCA_USER_TEMPLATE,
)

logger = logging.getLogger("chronos.llm")

_CHAT_ENDPOINT = "/chat/completions"
_TIMEOUT = 120.0  # seconds — RCA synthesis can take a moment

# Stored prompt-injection hardening (R-SEC-3): fields that flow from Graphiti
# (originally sourced from webhook payloads an attacker can influence) can
# contain triple-backticks, "IGNORE PREVIOUS INSTRUCTIONS", or other overrides.
# Before interpolating each evidence field into the prompt, clip length and
# neutralise sequences that would break out of the JSON code fence.
_MAX_FIELD_CHARS = 4_000


def _sanitize_evidence_field(value: Any) -> Any:
    """Recursively clip long strings and escape prompt-breaking sequences.

    - Strings over ``_MAX_FIELD_CHARS`` are truncated.
    - Triple-backticks are zero-width-joined so they can't close a fenced block.
    - Lines starting with "IGNORE PREVIOUS" / "DISREGARD" are prefixed with a
      safe marker that keeps the text readable but defuses the directive.
    """
    if isinstance(value, str):
        # Defang backticks BEFORE clipping so replacement can't expand past the limit.
        defanged = value.replace("```", "`​``")
        clipped = defanged[:_MAX_FIELD_CHARS]
        # Neutralise common prompt-injection directives.  Prefix the line with a
        # visible marker so auditors can spot attempted injections in Langfuse traces
        # without silently discarding the content.
        _INJECTION_PREFIXES = (
            "IGNORE PREVIOUS",
            "DISREGARD",
            "FORGET PREVIOUS",
            "NEW INSTRUCTIONS",
            "SYSTEM:",
            "USER:",
            "ASSISTANT:",
        )
        lines = clipped.split("\n")
        neutralized: list[str] = []
        for line in lines:
            stripped_upper = line.lstrip().upper()
            if any(stripped_upper.startswith(p) for p in _INJECTION_PREFIXES):
                neutralized.append("[INJECTION-ATTEMPT] " + line)
            else:
                neutralized.append(line)
        return "\n".join(neutralized)
    if isinstance(value, list):
        return [_sanitize_evidence_field(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize_evidence_field(v) for k, v in value.items()}
    return value


def _safe_json(obj: Any) -> str:
    """json.dumps with evidence sanitisation + default=str for tricky types."""
    return json.dumps(_sanitize_evidence_field(obj), indent=2, default=str)


def _litellm_headers() -> dict[str, str]:
    master_key = secret_or_none(settings.litellm_master_key)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if master_key:
        headers["Authorization"] = f"Bearer {master_key}"
    return headers


async def _call_litellm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """
    POST to LiteLLM proxy /chat/completions and return the assistant message content.

    Raises specific exceptions (httpx.HTTPStatusError, httpx.RequestError,
    asyncio.TimeoutError, ValueError) so callers can handle each case distinctly.
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
        inner_lines = []
        for line in lines[1:]:
            if line.strip() == "```":
                break
            inner_lines.append(line)
        raw = "\n".join(inner_lines).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        logger.error("LLM JSON payload was not an object; got %s", type(parsed).__name__)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM JSON response: %s\nRaw:\n%s", exc, raw[:500])
        return {}


def _synthesis_fallback(evidence: dict) -> dict[str, Any]:
    """Return a safe degraded RCA result when LLM synthesis fails."""
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


async def synthesize_rca(evidence: dict[str, Any]) -> dict[str, Any]:
    """
    Call LiteLLM proxy (chronos-synthesis model group) to synthesize a root cause
    analysis from the collected evidence dict.

    Returns a dict matching the RCA JSON schema, or a degraded fallback on failure.
    Each catch branch logs the specific error type to aid triage.
    """
    # Every evidence field passes through _safe_json, which clips length and
    # neutralises triple-backticks / known jailbreak phrases (R-SEC-3).
    user_message = RCA_USER_TEMPLATE.format(
        failed_test=_safe_json(evidence.get("failed_test", {})),
        affected_entity=_safe_json(evidence.get("affected_entity", {})),
        temporal_changes=_safe_json(evidence.get("temporal_changes", [])),
        schema_changes=_safe_json(evidence.get("schema_changes", [])),
        upstream_lineage=_safe_json(evidence.get("upstream_failures", [])),
        code_changes=_safe_json(evidence.get("related_code_files", [])),
        downstream_impact=_safe_json(evidence.get("downstream_assets", [])),
        audit_events=_safe_json(evidence.get("audit_events", [])),
        prior_incidents=_safe_json(evidence.get("prior_investigations", [])),
        business_impact_score=evidence.get("business_impact_score", "medium"),
        window_hours=str(settings.investigation_window_hours),
    )

    messages = [
        {"role": "system", "content": RCA_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await _call_litellm(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,
            max_tokens=2048,
        )
        result = _parse_json_response(raw)
        required = ("probable_root_cause", "root_cause_category", "confidence")
        if not result:
            raise ValueError("LiteLLM returned empty/non-JSON synthesis response")
        missing_fields = [key for key in required if key not in result]
        if missing_fields:
            raise ValueError(
                "LiteLLM synthesis response missing required fields: " + ", ".join(missing_fields)
            )
        logger.info(
            "RCA synthesis complete: category=%s, confidence=%s",
            result.get("root_cause_category"),
            result.get("confidence"),
        )
        return result
    except httpx.HTTPStatusError as exc:
        logger.error(
            "LiteLLM proxy returned HTTP %d: %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
    except httpx.RequestError as exc:
        logger.error("LiteLLM proxy unreachable: %r", exc)
    except TimeoutError:
        logger.error("LiteLLM synthesis timed out after %.0fs", _TIMEOUT)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("LiteLLM returned malformed response (%s): %s", type(exc).__name__, exc)

    # Shared fallback — only reached when one of the above catch blocks fired
    return _synthesis_fallback(evidence)


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
            model=settings.llm_model,
            messages=messages,
            temperature=0.0,
            max_tokens=1024,
        )
        return _parse_json_response(raw)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "LiteLLM extraction HTTP %d: %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
    except httpx.RequestError as exc:
        logger.error("LiteLLM extraction proxy unreachable: %r", exc)
    except TimeoutError:
        logger.error("LiteLLM extraction timed out")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("LiteLLM extraction malformed response (%s): %s", type(exc).__name__, exc)

    return {}
