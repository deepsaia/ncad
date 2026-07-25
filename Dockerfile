# ncad serve - single-node container image (Stage A).
#
# Stage B (a complete STATELESS, multi-replica deployment) is three interface swaps, and the current
# code was built so each is a single seam:
#   1. JobStore   -> define a JobStore protocol; add a RedisJobStore. The in-memory one stays the
#                    default for local ncad serve.
#   2. BuildPool  -> split into a producer (enqueue) and a separate ncad-worker process that
#                    consumes a queue. run_build is already the exact picklable unit a consumer runs
#                    (picklable args, writes to disk, no live handles). That was deliberate.
#   3. out/       -> an ArtifactStore abstraction (local dir vs object store keyed by
#                    <kind>/<name>/<file>) behind the catalog + artifact-serving handlers.
# None of this touches the ncad engine - it is all in the service layer. This image is stateful
# (in-memory job store, local out/) and single-node, which is correct for one replica.
#
# Target: linux/amd64 ONLY (cadquery-ocp + pyondsel ship manylinux x86_64 wheels; no aarch64).
# Build/run: see deploy/build.sh + deploy/run.sh.

# --- Stage 1: builder - resolve the locked venv ---
FROM --platform=linux/amd64 python:3.13-slim AS builder

# uv for a fast, reproducible frozen sync (copied from the official uv image).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Copy only what the sync needs, so a code-only change does not bust the dependency layer cache.
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Build the venv from the lockfile (no dev deps; installed non-editable so src/ need not be live).
RUN uv sync --frozen --no-dev --no-editable

# --- Stage 2: final - slim runtime ---
FROM --platform=linux/amd64 python:3.13-slim AS final

# Runtime system libs the OCP/pyrender wheels dynamically link (their native code is bundled, but
# these .so's are not in slim). --no-install-recommends + clean lists keep the layer small. The
# exact set is verified by importing the kernel in the built image (see deploy notes); add any lib
# a "libXXX.so.N: cannot open shared object file" import error names.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglu1-mesa \
        libxrender1 \
        libxext6 \
        libsm6 \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user owning /app.
RUN useradd -ms /bin/bash -u 1001 ncad

WORKDIR /app

# The resolved venv from the builder.
COPY --from=builder /app/.venv /app/.venv

# ncad serve resolves <root>/out + <root>/examples from the nearest pyproject.toml (ProjectRoot),
# and the build path reads materials/seed.hocon + schema/*.hocon relative to the source tree, so
# these must be present beside the app.
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY examples/ ./examples/
COPY materials/ ./materials/
COPY schema/ ./schema/

# Give the runtime user ownership of /app (so it can create out/ + write artifacts).
RUN mkdir -p /app/out && chown -R ncad:ncad /app

ENV PATH="/app/.venv/bin:$PATH" \
    NCAD_HOST=0.0.0.0 \
    NCAD_PORT=8000 \
    NCAD_DEV=0

# out/ is an OPTIONAL volume: with no -v the container uses an anonymous volume (artifacts do not
# persist across `docker rm`); with -v $PWD/out:/app/out they persist on the host.
VOLUME /app/out
EXPOSE 8000
USER ncad
ENTRYPOINT ["ncad", "serve"]
