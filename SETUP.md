# CHRONOS — Production Setup

Wire CHRONOS to live OpenMetadata + Graphiti backends in under 15 minutes.

> The default `.env` configuration runs CHRONOS against fixtures so you can
> smoke-test locally without external services. **Production deployments
> should follow this guide** to connect to a real OpenMetadata catalog and
> a managed FalkorDB (Graphiti's temporal knowledge graph backend).

---

## Prerequisites

- Python 3.11+
- Node 18+
- A Heroku account with deploy access to the `chronos-api` app (public URL: `chronos-api-0e8635fe890d.herokuapp.com`)
- A free GitHub account (for the Collate signup OAuth)

---

## 1. Provision FalkorDB Cloud (Free Tier)

[FalkorDB Cloud](https://app.falkordb.cloud/signup) gives you a free, hosted graph DB (Redis-wire-compatible, no card required for the MVP plan).

1. Sign up at <https://app.falkordb.cloud/signup>
2. Click **Create Database** → choose the **FREE** plan
3. Pick a region close to your CHRONOS dyno (e.g., `us-east-1` for Heroku US deployments)
4. Wait ~30 seconds for provisioning
5. Copy the connection details from the dashboard:
   - **Host** (e.g., `r-1234.falkor.cloud.falkordb.io`)
   - **Port** (typically `12345`)
   - **Password** (auto-generated)

Verify locally with `redis-cli`:
```bash
redis-cli -h <host> -p <port> -a <password> --tls PING
# Expected: PONG
```

---

## 2. Provision OpenMetadata

Pick **one** of two options. Collate Free is recommended (persistent state, real OAuth, supports webhooks).

### Option A — Collate Free Managed OpenMetadata (recommended)
1. Visit <https://www.getcollate.io>
2. Sign up for the **Free Tier** (managed cloud OM)
3. Once provisioned, go to **Settings → Integrations → Bots**
4. Create a bot named `chronos-agent` and **copy its JWT token**
5. Note your instance URL (e.g., `https://yourorg.collate.io`)

### Option B — Public OpenMetadata Sandbox
1. Visit <https://sandbox.open-metadata.org>
2. Log in with GitHub
3. Generate a JWT under **Settings → Bots**
4. Note: sandbox state is **ephemeral and may reset weekly**

### Configure the OpenMetadata Webhook → CHRONOS

In OM Settings → Webhooks → Add:
- **Name**: `chronos-rca`
- **Endpoint**: `https://chronos-api-0e8635fe890d.herokuapp.com/api/v1/webhooks/openmetadata`
- **Event Filters**: Test Case Failures, Schema Changes
- **Secret Key**: paste the value of `WEBHOOK_HMAC_SECRET` from your `.env`
- **Active**: ✅

---

## 3. Push Config to Heroku

Use the helper script for guided setup:
```bash
./scripts/setup_production.sh
```

Or set vars directly:
```bash
heroku config:set \
  FALKORDB_HOST=<host> \
  FALKORDB_PORT=<port> \
  FALKORDB_PASSWORD=<password> \
  OPENMETADATA_HOST=https://yourorg.collate.io \
  OPENMETADATA_JWT_TOKEN=eyJ... \
  -a chronos-api
```

Restart the dyno so new vars are picked up:
```bash
heroku ps:restart -a chronos-api
```

---

## 4. Verify Live Connections

Hit the new component health endpoint:
```bash
curl https://chronos-api-0e8635fe890d.herokuapp.com/api/v1/health/components | jq
```

Expected:
```json
{
  "overall": "healthy",
  "components": [
    {"name": "openmetadata", "state": "healthy", "latency_ms": 124, ...},
    {"name": "falkordb",     "state": "healthy", "latency_ms":  38, ...},
    {"name": "litellm",      "state": "healthy", "latency_ms": 312, ...},
    {"name": "slack",        "state": "healthy", ...}
  ]
}
```

The frontend nav badge should now show a **green dot** with "Live".

---

## 5. Seed Historical Demo Data (Optional but Recommended)

For the dashboard to look impressive on first load, populate Graphiti with synthetic past incidents:

```bash
# Run inside a Heroku one-off dyno or locally with prod env vars sourced
python -m chronos.demo seed --count 30
```

This creates 30 plausibly-distributed historical incidents over the past 30 days. Re-run with `--clear` to reset.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Badge shows red dot, FalkorDB down | TLS not enabled in connection | FalkorDB Cloud requires TLS; the redis-py client auto-detects from port; if needed add `FALKORDB_TLS=true` |
| OpenMetadata returns 401 | Stale JWT token | Regenerate the bot token in OM and `heroku config:set` again |
| LiteLLM probe DOWN but Groq key set | LITELLM_PROXY_URL pointing at non-existent proxy | Either point to Groq directly (`https://api.groq.com/openai/v1`) or remove the var to fall back to direct provider mode |
| Webhook payloads not arriving | HMAC secret mismatch | Verify `WEBHOOK_HMAC_SECRET` matches the value pasted in OM webhook config |

For deeper observability, tail Heroku logs:
```bash
heroku logs --tail -a chronos-api
```

---

## Reverting to Fixture Mode

If a backing service goes down during a demo, set `DEMO_MODE=true`:
```bash
heroku config:set DEMO_MODE=true -a chronos-api
heroku ps:restart -a chronos-api
```

CHRONOS will fall back to the in-process fixtures and the demo flow continues uninterrupted.
