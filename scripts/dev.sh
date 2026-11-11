#!/usr/bin/env bash
# Local development: databases + Temporal in Docker, app processes from source with reload.
#
#   make dev                         # everything
#   SKIP_INFRA=1 make dev            # reuse databases you already run (set DB_URL)
#   WORKER=0 make dev                # don't start the Temporal worker
#
# Ctrl+C stops every process this script started (containers keep running;
# `make infra-down` stops them).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose -f "$ROOT/deploy/docker-compose.yml")
DB_URL="${DB_URL:-postgresql://driftless:driftless@localhost:5432/driftless}"
API_PORT="${API_PORT:-8000}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "error: '$1' is required ($2)" >&2; exit 1; }; }
need uv "https://docs.astral.sh/uv/"
need pnpm "corepack enable"

# Prefix each line of a process's output with a coloured label.
run() {
  local name="$1" color="$2"; shift 2
  ( "$@" 2>&1 | sed -u "s/^/$(printf '\033[%sm%-6s\033[0m| ' "$color" "$name")/" ) &
}

cleanup() { trap - INT TERM EXIT; kill 0 2>/dev/null || true; }
trap cleanup INT TERM EXIT

if [[ "${SKIP_INFRA:-0}" != "1" ]]; then
  need docker "https://docs.docker.com/get-docker/"
  echo "▶ starting databases and Temporal…"
  "${COMPOSE[@]}" up -d metadata-db pg-source temporal
  echo "▶ waiting for the metadata database…"
  for _ in $(seq 1 60); do
    "${COMPOSE[@]}" exec -T metadata-db pg_isready -U driftless -d driftless >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "▶ installing dependencies (fast when already installed)…"
(cd "$ROOT/backend" && uv sync -q)
(cd "$ROOT/frontend" && pnpm install --silent)

echo "▶ applying metadata-DB migrations…"
(cd "$ROOT/backend" && DRIFTLESS_DATABASE_URL="$DB_URL" uv run driftless-api-migrate upgrade)

export DRIFTLESS_DATABASE_URL="$DB_URL"
export SAMPLE_SOURCE_PW="${SAMPLE_SOURCE_PW:-source}"

run api "36" bash -c "cd '$ROOT/backend' && uv run uvicorn driftless_api.main:create_app --factory --reload --port $API_PORT"
if [[ "${WORKER:-1}" == "1" ]]; then
  # Retry so the worker survives Temporal starting slowly.
  run worker "35" bash -c "cd '$ROOT/backend' && until uv run driftless-worker; do echo 'worker exited; retrying in 3s'; sleep 3; done"
fi
run web "32" bash -c "cd '$ROOT/frontend' && pnpm --filter @driftless/web dev --port 5173 --strictPort"

cat <<EOF

  Driftless is starting:
    Web app      http://localhost:5173
    API docs     http://localhost:${API_PORT}/api/v1/docs
    Temporal UI  http://localhost:8233
  Sample source: host localhost, port 5433, database shop, user source,
                 password reference env:SAMPLE_SOURCE_PW

  Press Ctrl+C to stop.

EOF
wait
