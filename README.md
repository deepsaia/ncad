# ncad

**A declarative, parametric and direct CAD/CAM/CAE/PCB engine.** Define a part as a
text document (HOCON/JSON/YAML) and a pure executor replays it against an
exact-geometry kernel to produce solids, and (over the roadmap) assemblies, motion,
drawings, and more. No authoring GUI; a strong browser viewer for seeing. The same
document is editable by a human, an agent, or a generator, and rebuilds
deterministically.

## Documents

- [`docs/design.md`](./docs/design.md): the target-engine design (*what* and *why*).
- [`docs/plan.md`](./docs/plan.md): phased, bucketed build order and tracker.
- [`docs/research/`](./docs/research/): sourced decisions (kernel choice, TNP, CAM, PCB).
- [`CLAUDE.md`](./CLAUDE.md): coding guidelines and best practices.

## Core idea

One-way data flow; the document is the single source of truth:

```
author (human / agent / generator)  >>  document (dict)  >>  build(document) >> model  >>  view / export
        (all authoring here)                              (pure, deterministic)
```

A part is an ordered **feature tree**. Each feature `op` dispatches to a pure builder
`(shape_in, params, provenance_in, kernel) >> OpResult`, threaded by the `Builder`.
The kernel (build123d / OCCT today) sits behind a swappable interface.

## Setup

Requires Python 3.13, managed via [`uv`](https://docs.astral.sh/uv/). One dependency
(`pyondsel`, the OndselSolver multibody bindings used for motion) is a local editable
checkout: clone it beside this repo before `uv sync` (it needs a C++17 compiler + CMake).

```bash
git clone https://github.com/deepsaia/pyondsel ../pyondsel   # motion solver (side-by-side)
uv sync                        # install deps into .venv
uv run pytest -m "not slow"    # fast suite (no OCP import)
uv run pytest -m slow          # kernel + end-to-end (real build123d geometry)
```

If you do not have the side-by-side `pyondsel` checkout, see the comment in
[`pyproject.toml`](./pyproject.toml) for the git-source fallback.

## Quickstart

Build a feature-tree document to glTF, then view it in the browser:

```bash
ncad build examples/gate-0.2/bracket.hocon   # writes out/bracket.glb
ncad view                                     # serve ./out at http://127.0.0.1:8000
```

Open http://127.0.0.1:8000 and pick a model. `ncad` runs from any subdirectory of the
project; the models directory defaults to `<project-root>/out`. Bare `ncad` is the same
as `ncad view`.

## Running ncad

The `ncad` command (a typer app) is the single entrypoint. The two everyday commands:

| Command | What it does |
| --- | --- |
| `ncad build <document> [--out DIR]` | Build every part in a feature-tree document to `<part>.glb` (plus its BOM / plan / element-map sidecars). |
| `ncad view [DIR]` (or bare `ncad`) | Launch the lightweight stdlib browser 3D viewer + local model-manager over a models directory (default `out/`). |
| `ncad serve [DIR]` | Run the full HTTP service (Tornado): versioned JSON API under `/api/v1`, the viewer SPA at `/viewer`, Swagger UI at `/docs`, and dev hot-reload. |

Common flags for `ncad view` / `ncad serve`: `--host` (default `127.0.0.1`), `--port`
(default `8000`, `0` picks a free port), `--dev` / `--no-dev` (hot-reload; on by default).

Author documents are the input; you never hand-edit geometry. Build one document:

```bash
ncad build examples/gate-6.0/crank_slider.hocon --out out
```

or drive the whole model-manager from the viewer (below).

### The viewer

`ncad view` serves a browser app that is also a local model-manager: pick an example
spec from the searchable tree, click Build to run it, and the model appears in the
models list; each model has hover actions to regenerate (rebuild from its recorded
source) or delete it. It has three modes:

- **Parts** - build and inspect a single feature-tree document.
- **Assemblies** - compose an `.asm.hocon` (instances + mates/joints) into a scene.
- **Motion** - drive a `.motion.hocon` study and scrub the resulting trajectory on a timeline.

The sidebar is resizable (width persists). `ncad view` runs with hot-reload by default
(`--no-dev` to serve the cached page).

### The HTTP service (`ncad serve`)

`ncad serve` runs the same viewer on a Tornado HTTP service that also exposes a versioned
JSON API, so a future frontend (e.g. React) can be built against a stable contract:

| Route | Serves |
| --- | --- |
| `/` | 302 redirect to `/viewer` |
| `/viewer` (and `/viewer/<model>.glb`) | the viewer SPA (deep link preselects a model) |
| `/api/v1/...` | the JSON API (specs, models, assemblies, motions, build/assemble/motion-build, sidecars) |
| `/api/v1/models/<name>` | model bytes (glb/gltf/bin/png) |
| `/api/v1/openapi.json` | the OpenAPI 3.1 document |
| `/docs` | interactive Swagger UI |

In dev mode (default), it hot-reloads two ways: editing any `src/ncad` source restarts the
server automatically (tornado.autoreload), and the open viewer tab reloads itself over a
websocket (`/ws/livereload`) after the restart. Run `ncad serve --no-dev` for a stable,
non-reloading server. The lighter `ncad view` (stdlib, no extra routes) remains for a quick
look without the API surface.

Viewer settings (display mode, material, lighting, scene toggles, reset, and the
BOM/Plan panels) live in a translucent floating controls panel over the viewport. It
uses icons by default (labels on hover, or toggle "show labels"), can be dragged and
snapped to any edge or anchored to a corner, and all its state persists across reloads.

A theme toggle in the sidebar top bar cycles light / system / dark; "system" follows
the OS preference live. The 3D viewport recolors with the theme, and the choice
persists across reloads.

## Examples and gates

Each roadmap gate has a self-contained example under `examples/gate-<id>-<name>/`. They
double as user-facing samples and as a regression net: every example is built and
checked by the test suite, so each gate stays a living, tested artifact.

- `examples/gate-0.1-first-shape/block.hocon`: a rectangle sketched on XY, extruded
  into a block. Proves the spine: document >> build >> glTF >> view.
- `examples/gate-0.2/`: the everyday ops + expressions (a parametric bracket, and a
  concentric hex boss). Proves pocket/hole/fillet/chamfer/boolean + the expression layer.

## Status

**Phase 0 bucket 0.2 complete:** on top of the bucket 0.1 spine, the everyday op
vocabulary (pocket, hole, fillet, chamfer, boolean; circle/polygon sketches) plus a
parametric expression layer (`${ref}` + arithmetic + registered functions) build the
boring bracket from a parametric document. See [`docs/plan.md`](./docs/plan.md) for the
live tracker.
