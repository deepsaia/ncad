#!/bin/bash
# Run the ncad serve container. Usage: deploy/run.sh [--persist] [extra docker args...].
#   --persist  bind-mount ./out so build artifacts survive `docker rm` (otherwise ephemeral).
# Config: pass an env file with NCAD_RUN_ENV_FILE=path (defaults to ./.env if present).
set -euo pipefail

SERVICE_TAG="${SERVICE_TAG:-ncad}"
SERVICE_VERSION="${SERVICE_VERSION:-latest}"
HOST_PORT="${NCAD_PORT:-8000}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RUN_ARGS=(-p "${HOST_PORT}:8000")

# Optional persistence: bind-mount ./out only when --persist is given (out/ is an optional volume).
if [ "${1:-}" == "--persist" ]; then
    mkdir -p "${REPO_ROOT}/out"
    RUN_ARGS+=(-v "${REPO_ROOT}/out:/app/out")
    shift
fi

# Optional env file (NCAD_* knobs). Default to ./.env if present.
ENV_FILE="${NCAD_RUN_ENV_FILE:-${REPO_ROOT}/.env}"
if [ -f "${ENV_FILE}" ]; then
    RUN_ARGS+=(--env-file "${ENV_FILE}")
fi

echo "ncad viewer will be at http://localhost:${HOST_PORT}/viewer (Ctrl+C to stop)"
exec docker run --rm --platform linux/amd64 "${RUN_ARGS[@]}" "$@" \
    "${SERVICE_TAG}:${SERVICE_VERSION}"
