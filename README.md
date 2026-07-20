# ncad

**A declarative, parametric and direct CAD/CAM/CAE/PCB engine.** Define a part as a
text document (HOCON/JSON/YAML) and a pure executor replays it against an
exact-geometry kernel to produce solids, and (over the roadmap) assemblies, motion,
drawings, and more. No authoring GUI; a strong browser viewer for seeing. The same
document is editable by a human, an agent, or a generator, and rebuilds
deterministically.

## Documents

- [`docs/documentation-design.md`](./docs/documentation-design.md): the documentation site's
  information architecture (the Docusaurus Learn + ncad two-part model).
- [`docs/feature-ordering.md`](./docs/feature-ordering.md): op-composition rules (safe order +
  failure mode per op).
- [`CLAUDE.md`](./CLAUDE.md): coding guidelines and best practices.

The code is the source of truth for what ncad can actually do: the op registry
(`src/ncad/ops/op_registry.py`), the schemas (`schema/*.hocon`), and the shipped `examples/`.

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
ncad build examples/03-dress-up/shelf_bracket.hocon   # writes out/shelf_bracket.glb
ncad view                                             # serve ./out at http://127.0.0.1:8000
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
ncad build examples/02-solid-features/revolved_washer.hocon --out out
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

## Examples

Curated example documents live under `examples/`, organized by capability (sketching, solid
features, dress-up, patterns/multibody, direct modeling, assemblies, motion, and end-to-end
showcases). Build any of them with `ncad build <path>` and view with `ncad view`.

## Status

The core engine is built: parametric feature modeling (2D sketching + constraint solver,
sketched + dress-up solid features, patterns/booleans/multibody, a persistent-name layer with
direct/synchronous edits), assemblies (mates + lower-pair joints), forward-kinematics motion
(drivers + gear/cam/slot couplings), an agent-facing validation + diagnostics contract, and a
browser viewer + HTTP service. Geometry is build123d/OCCT; sketch constraints are py-slvs; motion
is OndselSolver via pyondsel.

## Future roadmap / possible directions

Not built; recorded as directions rather than commitments:

- **Drafting & documentation** (2D drawings via HLR: views, dimensions, annotations, tables).
- **PMI / GD&T** (semantic geometric-tolerance annotations on model elements).
- **Surfacing & freeform** (Class A stays out of scope unless a specialist module is adopted).
- **Convergent modeling** (mesh + B-rep in one model).
- **Domain profiles** (sheet-metal, mold, building). Not needed yet: the furniture and house
  showcases demonstrate the general substrate already reaches these without dedicated profiles;
  kept as future potential.
- **Large-assembly performance** (lightweight reps, LOD, spatial index, out-of-context cache).
- **Interchange & plugins** (IGES / STL / 3MF / DXF; a plugin contract; PartCAD; OpenSCAD import)
  and **analysis export seams** (delegate every solve: FEA to CalculiX/Elmer/Z88, 1D frame to
  frame3dd/PyNite, CFD to Elmer, pipe-network to EPANET, all as input-deck exporters, never a
  solver we write).
- **Multibody dynamics & robotics** (gravity, forces, springs, contact >> reaction forces; and
  contact-rich robotics sim) via a real physics engine (MuJoCo/Bullet) as a first-class
  force-driven backend. Deferred here because OndselSolver as vendored is kinematics-only.
- **CAM** (a process profile over a built solid >> toolpaths >> G-code) and **PCB/ECAD**
  (a board data model + DRC + lowering to solids, KiCad round-trip).
