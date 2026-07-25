#!/bin/bash
# Build the ncad serve container image (linux/amd64; the OCP/pyondsel wheels are x86_64-only).
# Usage: deploy/build.sh [--no-cache]. Tag overridable via SERVICE_TAG / SERVICE_VERSION.
set -euo pipefail

SERVICE_TAG="${SERVICE_TAG:-ncad}"
# Default version = the pyproject version, else a date stamp. Read without importing the package.
SERVICE_VERSION="${SERVICE_VERSION:-$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')}"
SERVICE_VERSION="${SERVICE_VERSION:-dev}"

CACHE_ARGS="--rm"
if [ "${1:-}" == "--no-cache" ]; then
    CACHE_ARGS="--no-cache --progress=plain"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Building ${SERVICE_TAG}:${SERVICE_VERSION} for linux/amd64 from ${REPO_ROOT}"

# shellcheck disable=SC2086
DOCKER_BUILDKIT=1 docker build \
    -t "${SERVICE_TAG}:${SERVICE_VERSION}" \
    -t "${SERVICE_TAG}:latest" \
    --platform linux/amd64 \
    ${CACHE_ARGS} \
    "${REPO_ROOT}"

echo "Built ${SERVICE_TAG}:${SERVICE_VERSION} (also tagged :latest)"
