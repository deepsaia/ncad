# HTTP API reference

`ncad serve` runs a Tornado service exposing a versioned JSON API under `/api/v1`, the viewer SPA at
`/viewer`, and Swagger UI at `/docs` (backed by `/api/v1/openapi.json`). Responses use a shared error
envelope `{"error": <message>}` and permissive CORS. Build endpoints are asynchronous jobs; a few
action endpoints are synchronous.

(The lighter `ncad view` stdlib server exposes the same resources under **unversioned** `/api/...`
paths and runs builds synchronously; it has no jobs, Swagger, or websocket. The versioned API below is
the one to build against.)

## Pages and docs

| Method | Path | Serves |
| --- | --- | --- |
| GET | `/` | 302 redirect to `/viewer` |
| GET | `/viewer`, `/viewer/<model>` | the viewer SPA (deep link preselects a model) |
| GET | `/js/<file>` | viewer JS modules |
| GET | `/docs` | Swagger UI |
| GET | `/api/v1/openapi.json` | the OpenAPI 3.1 document |

## Collections (GET)

| Path | Response |
| --- | --- |
| `/api/v1/specs` | `{"tree": [...]}` example-spec tree |
| `/api/v1/models` | `{"models": [{name, source}, ...]}` |
| `/api/v1/assemblies` | `{"assemblies": [name, ...]}` |
| `/api/v1/motions` | `{"motions": [{name, label}, ...]}` |
| `/api/v1/robots` | `{"robots": [{name, label}, ...]}` |
| `/api/v1/analyses` | `{"analyses": [{name, label, source}, ...]}` |

## Detail resources (GET; 200 or 404)

`/api/v1/motion/<name>`, `/api/v1/analysis/<name>`, `/api/v1/analysis-mesh/<name>`,
`/api/v1/robot/<name>`, `/api/v1/robot-sweeps/<name>`, `/api/v1/assembly/<name>`,
`/api/v1/bom/<name>`, `/api/v1/plan/<name>` (SVG), `/api/v1/elementmap/<name>`,
`/api/v1/hierarchy/<name>`, `/api/v1/status/<name>`, and `/api/v1/models/<name>` (model bytes:
glb/gltf/bin/png, MIME by extension).

`/api/v1/robot-keyframes/<name>` is GET (read sets) + POST (upsert a keyframe set).

## Build endpoints (async jobs)

POST with body `{"spec": <path-or-source>}`. Each submits a job and returns `202 {"job_id": ...}`
(`400` bad body, `503` when the queue is saturated):

| Path | Job result |
| --- | --- |
| `/api/v1/build` | `{models, built, build_ms}` |
| `/api/v1/assemble` | `{assemblies, assembled, issues}` |
| `/api/v1/motion-build` | `{motions, assembled, issues}` |
| `/api/v1/physics-build` | `{robots, robot, warnings}` |
| `/api/v1/analyze` | `{analyses, analysis, status}` |

Poll a job with `GET /api/v1/jobs/<id>` (404 if unknown/evicted); cancel with
`POST /api/v1/jobs/<id>/cancel`. Job status: `{status, kind, stage, stages_done, stages_total,
message}`, plus `result` when done and `error` when failed/cancelled. `status` is one of
`queued | running | done | failed | cancelled`.

## Synchronous actions (POST)

- `/api/v1/robot-collide` - `{name, pose}` -> `{collisions: [...]}` (live self-collision check).
- `/api/v1/export` - `{name, kind, format}` -> a file download (attachment).
- `/api/v1/validate` - `{spec}` -> `{ok, diagnostics}` (200 even when `ok=false`).

## Deletes (POST) and websocket

`POST /api/v1/models/<name>/delete`, `/api/v1/assembly/<name>/delete`, `/api/v1/robot/<name>/delete`,
`/api/v1/analysis/<name>/delete` each return the updated list (or 404). In dev mode a websocket at
`/ws/livereload` announces server restarts to the open viewer tab.

## Configuration (`NCAD_*`)

The service is configured entirely by environment variables (see the repo `.env.example`); precedence
is CLI flag > env > default.

| Env var | Default | Meaning |
| --- | --- | --- |
| `NCAD_HOST` | `127.0.0.1` | bind address |
| `NCAD_PORT` | `8000` | bind port (`0` = ephemeral) |
| `NCAD_DEV` | `0` | hot-reload (server autoreload + browser live-reload) |
| `NCAD_MAX_WORKERS` | auto `max(1, min(4, cpu-2))` | spawn process-pool size |
| `NCAD_MAX_CONCURRENT_BUILDS` | = max_workers | in-flight builds before queueing |
| `NCAD_JOB_QUEUE_MAX` | `32` | queued-job bound; submit returns 503 past it |
| `NCAD_JOB_TTL` | `300.0` | seconds a finished job is retained |
| `NCAD_JOB_POLL_MS` | `400` | frontend job-status poll interval |
| `NCAD_SHUTDOWN_TIMEOUT` | `30.0` | seconds to drain in-flight builds on shutdown |
| `NCAD_JOBS_DIR` | `<models>/.jobs` | per-job progress-file dir |
| `NCAD_CCX` | search PATH | explicit CalculiX `ccx` path (for FEA) |

For running the service in a container, see the repo's "Running in Docker" README section.
