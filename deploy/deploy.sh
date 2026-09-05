#!/usr/bin/env bash
#
# Server-side deploy: move the checkout to origin/<branch>, rebuild the stack,
# and roll the code back if the new container does not become healthy.
#
# Run from anywhere; it resolves the repository root itself. Intended to be
# invoked over SSH by .github/workflows/ci.yml, but it is safe to run by hand.
#
# The whole body lives in main() on purpose: the update rewrites this very
# file, and bash reads a plain script incrementally, so a release that changes
# deploy.sh could otherwise resume mid-file and execute garbage. Wrapping it in
# a function forces bash to parse everything before the first command runs.
set -euo pipefail

main() {
    local BRANCH="${DEPLOY_BRANCH:-main}"
    local HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8099/health/}"
    local HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-120}"

    cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    # .env and volumes/ are gitignored, so neither the checkout nor the rebuild
    # touches the server's secrets, database or uploaded media.
    if [[ ! -f .env ]]; then
        log "ERROR: .env is missing in $PWD -- the container will not start."
        return 1
    fi

    local previous target
    previous="$(git rev-parse HEAD)"
    log "current commit: $previous on branch $(git rev-parse --abbrev-ref HEAD)"

    git fetch --prune origin "$BRANCH"
    target="$(git rev-parse "origin/$BRANCH")"

    if [[ "$previous" == "$target" ]]; then
        log "already at origin/$BRANCH; making sure the stack is up"
        compose up -d
        wait_healthy "$HEALTH_URL" "$HEALTH_TIMEOUT" && {
            log "healthy, nothing to deploy"
            return 0
        }
        log "ERROR: stack is unhealthy at the current commit"
        compose logs --tail 50 server
        return 1
    fi

    log "deploying $previous -> $target"
    # checkout -B, not reset --hard: reset moves whichever branch happens to be
    # checked out, leaving the server on a stale branch name that merely points
    # at the deployed commit.
    git checkout -B "$BRANCH" "$target"

    if compose up -d --build && wait_healthy "$HEALTH_URL" "$HEALTH_TIMEOUT"; then
        log "deployed $target on branch $BRANCH successfully"
        # Keep the disk from filling up with superseded build layers.
        docker image prune -f >/dev/null || true
        return 0
    fi

    log "ERROR: $target did not become healthy within ${HEALTH_TIMEOUT}s; rolling back"
    compose logs --tail 80 server || true

    git reset --hard "$previous"
    if compose up -d --build && wait_healthy "$HEALTH_URL" "$HEALTH_TIMEOUT"; then
        log "rolled back to $previous"
    else
        log "FATAL: rollback to $previous is also unhealthy -- manual intervention needed"
    fi
    # NOTE: this rolls back code only. Migrations applied by the entrypoint are
    # NOT reverted; if a release migrates the schema, plan its rollback separately.
    return 1
}

log() { printf '==> %s\n' "$*"; }

compose() { docker compose --profile prod "$@"; }

wait_healthy() {
    local url="$1" timeout="$2"
    local deadline=$((SECONDS + timeout))
    while ((SECONDS < deadline)); do
        if curl -fsS -m 5 "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 3
    done
    return 1
}

main "$@"
