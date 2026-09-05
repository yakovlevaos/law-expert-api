#!/usr/bin/env bash
#
# Server-side deploy: fast-forward the checkout to origin/<branch>, rebuild the
# stack, and roll the code back if the new container does not become healthy.
#
# Run from anywhere; it resolves the repository root itself. Intended to be
# invoked over SSH by .github/workflows/ci.yml, but it is safe to run by hand.
set -euo pipefail

BRANCH="${DEPLOY_BRANCH:-main}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8099/health/}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-120}"

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { printf '==> %s\n' "$*"; }

compose() { docker compose --profile prod "$@"; }

wait_healthy() {
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    while ((SECONDS < deadline)); do
        if curl -fsS -m 5 "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 3
    done
    return 1
}

# .env and volumes/ are gitignored, so neither reset nor rebuild touches the
# server's secrets, database or uploaded media.
if [[ ! -f .env ]]; then
    log "ERROR: .env is missing in $PWD -- the container will not start."
    exit 1
fi

previous="$(git rev-parse HEAD)"
log "current commit: $previous"

git fetch --prune origin "$BRANCH"
target="$(git rev-parse "origin/$BRANCH")"

if [[ "$previous" == "$target" ]]; then
    log "already at origin/$BRANCH; making sure the stack is up"
    compose up -d
    wait_healthy && { log "healthy, nothing to deploy"; exit 0; }
    log "ERROR: stack is unhealthy at the current commit"
    compose logs --tail 50 server
    exit 1
fi

log "deploying $previous -> $target"
git reset --hard "$target"

if compose up -d --build && wait_healthy; then
    log "deployed $target successfully"
    # Keep the disk from filling up with superseded build layers.
    docker image prune -f >/dev/null || true
    exit 0
fi

log "ERROR: $target did not become healthy within ${HEALTH_TIMEOUT}s; rolling back"
compose logs --tail 80 server || true

git reset --hard "$previous"
if compose up -d --build && wait_healthy; then
    log "rolled back to $previous"
else
    log "FATAL: rollback to $previous is also unhealthy -- manual intervention needed"
fi
# NOTE: this rolls back code only. Migrations applied by the entrypoint are
# NOT reverted; if a release migrates the schema, plan its rollback separately.
exit 1
