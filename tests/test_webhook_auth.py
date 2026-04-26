from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from chronos.config.settings import settings
from chronos.main import app


@pytest.fixture(autouse=True)
def _restore_webhook_settings():
    original_required = settings.webhook_signature_required
    original_secret = settings.webhook_hmac_secret
    yield
    settings.webhook_signature_required = original_required
    settings.webhook_hmac_secret = original_secret


@pytest.fixture(autouse=True)
def _stub_webhook_background_tasks(monkeypatch: pytest.MonkeyPatch):
    async def _noop(*_args, **_kwargs):
        return True

    monkeypatch.setattr("chronos.api.routes.webhooks.ingest_om_event", _noop)
    monkeypatch.setattr("chronos.api.routes.webhooks.receive_openlineage_event", _noop)


def _sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _payload_bytes() -> bytes:
    payload = {
        "eventType": "ENTITY_UPDATED",
        "entityType": "table",
        "entityFullyQualifiedName": "sample_db.default.orders",
        "entity": {"name": "orders"},
    }
    return json.dumps(payload).encode("utf-8")


def test_valid_signature_accepted():
    settings.webhook_signature_required = True
    settings.webhook_hmac_secret = SecretStr("test-secret")

    body = _payload_bytes()
    signature = _sign(body, "test-secret")

    client = TestClient(app)
    response = client.post(
        "/api/v1/webhooks/openmetadata",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-OM-Signature": signature,
        },
    )
    assert response.status_code == 200


def test_invalid_signature_rejected():
    settings.webhook_signature_required = True
    settings.webhook_hmac_secret = SecretStr("test-secret")

    client = TestClient(app)
    response = client.post(
        "/api/v1/webhooks/openmetadata",
        content=_payload_bytes(),
        headers={
            "Content-Type": "application/json",
            "X-OM-Signature": "sha256=invalid",
        },
    )
    assert response.status_code == 401


def test_missing_signature_rejected_when_required():
    settings.webhook_signature_required = True
    settings.webhook_hmac_secret = SecretStr("test-secret")

    client = TestClient(app)
    response = client.post(
        "/api/v1/webhooks/openmetadata",
        content=_payload_bytes(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_unsigned_accepted_in_dev_mode():
    settings.webhook_signature_required = False
    settings.webhook_hmac_secret = None

    client = TestClient(app)
    response = client.post(
        "/api/v1/webhooks/openmetadata",
        content=_payload_bytes(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
