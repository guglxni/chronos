#!/usr/bin/env bash
#
# Guided production setup for CHRONOS.
#
# Prompts for FalkorDB + OpenMetadata credentials and pushes them to the
# configured Heroku app. Idempotent — safe to re-run.
#
# Usage:
#   ./scripts/setup_production.sh                    # default app
#   HEROKU_APP=my-other-app ./scripts/setup_production.sh
#

set -euo pipefail

HEROKU_APP="${HEROKU_APP:-chronos-api-0e8635fe890d}"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
dim()  { printf '\033[2m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()  { printf '\033[31m%s\033[0m\n' "$*"; }

echo
bold "CHRONOS Production Setup"
echo "════════════════════════════════════════════════════════════"
dim "Target Heroku app: $HEROKU_APP"
echo

# ── Prereq: heroku CLI ───────────────────────────────────────────────────
if ! command -v heroku >/dev/null 2>&1; then
    red "✗ Heroku CLI not found. Install from https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

if ! heroku auth:whoami >/dev/null 2>&1; then
    red "✗ Not logged in to Heroku. Run: heroku login"
    exit 1
fi

if ! heroku apps:info -a "$HEROKU_APP" >/dev/null 2>&1; then
    red "✗ Cannot access app '$HEROKU_APP'. Verify access or set HEROKU_APP env var."
    exit 1
fi

green "✓ Heroku CLI ready, authenticated, app accessible"
echo

# ── Helper: prompt with optional default and silent flag ─────────────────
prompt() {
    # prompt <var_name> <description> [silent=0|1]
    local var=$1 desc=$2 silent=${3:-0}
    local current
    current=$(heroku config:get "$var" -a "$HEROKU_APP" 2>/dev/null || true)

    if [[ -n "$current" ]]; then
        printf '  %s is already set. Replace? [y/N] ' "$var"
        read -r reply
        if [[ "$reply" != "y" && "$reply" != "Y" ]]; then
            dim "    → keeping existing value"
            return
        fi
    fi

    local value
    if [[ "$silent" == "1" ]]; then
        printf '  %s: ' "$desc"
        read -rs value
        echo
    else
        printf '  %s: ' "$desc"
        read -r value
    fi

    if [[ -z "$value" ]]; then
        dim "    → skipped (empty)"
        return
    fi

    heroku config:set "$var=$value" -a "$HEROKU_APP" >/dev/null
    green "    ✓ $var set"
}

# ── FalkorDB ─────────────────────────────────────────────────────────────
bold "1/3 — FalkorDB Cloud connection"
dim "    Sign up free at https://app.falkordb.cloud/signup"
echo
prompt FALKORDB_HOST     "FalkorDB host (e.g. r-1234.falkor.cloud.falkordb.io)" 0
prompt FALKORDB_PORT     "FalkorDB port (e.g. 12345)" 0
prompt FALKORDB_PASSWORD "FalkorDB password" 1
echo

# ── OpenMetadata ─────────────────────────────────────────────────────────
bold "2/3 — OpenMetadata connection"
dim "    Either Collate Free (https://www.getcollate.io) or sandbox.open-metadata.org"
echo
prompt OPENMETADATA_HOST       "OpenMetadata base URL (https://...)" 0
prompt OPENMETADATA_JWT_TOKEN  "OpenMetadata bot JWT token" 1
echo

# ── Optional: Slack ──────────────────────────────────────────────────────
bold "3/3 — Slack notifications (optional)"
dim "    Skip with empty input"
echo
prompt SLACK_WEBHOOK_URL "Slack incoming webhook URL" 1
echo

# ── Restart dyno ─────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
bold "Restarting Heroku dyno to pick up new config…"
heroku ps:restart -a "$HEROKU_APP" >/dev/null
green "✓ Restarted"
echo

# ── Verify ───────────────────────────────────────────────────────────────
bold "Verifying live connections (polling /api/v1/health/components)…"
echo

api_url=$(heroku apps:info -a "$HEROKU_APP" --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["app"]["web_url"])')
api_url="${api_url%/}"
endpoint="$api_url/api/v1/health/components"

# Wait up to 30s for dyno restart, then check
for i in {1..15}; do
    sleep 2
    if response=$(curl -fsS "$endpoint" 2>/dev/null); then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        echo
        overall=$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["overall"])' 2>/dev/null || echo unknown)
        if [[ "$overall" == "healthy" ]]; then
            green "✓ All components healthy. Setup complete."
        else
            red "⚠ Overall state: $overall — review the per-component detail above and check Heroku logs:"
            echo "    heroku logs --tail -a $HEROKU_APP"
        fi
        exit 0
    fi
    dim "    waiting for dyno… ($i/15)"
done

red "✗ Could not reach $endpoint after 30s. Check: heroku logs --tail -a $HEROKU_APP"
exit 1
