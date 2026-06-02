# ncad

**Prompt → 3D models.** An agent, given a natural-language prompt and a parametric
modeling toolkit, writes and edits a declarative model and renders it to 3D objects,
scenes, and architecture. Architecture-first.

## Documents

- [`design.md`](./design.md) — the validated system design (*what* and *why*).
- [`plan.md`](./plan.md) — phased build order and progress tracker.
- [`CLAUDE.md`](./CLAUDE.md) — coding guidelines & best practices.
- [`docs/design_ideas.md`](./docs/design_ideas.md) — background reasoning.

## Core idea

Three layers, one-way data flow:

```
generate(seed, params) → spec  →  build(spec) → geometry  →  render / export / BOM
   (all randomness)        (pure function, deterministic)
```

The **spec** (a validatable dict) is the single source of truth. The **builder** is
pure. The **generator** isolates all randomness.

## Setup

Requires Python 3.13 (managed via [`uv`](https://docs.astral.sh/uv/)).

```bash
uv sync                 # install core deps into .venv
uv run pytest           # run the test suite
```

Optional dependency groups:

```bash
uv sync --extra interchange   # ezdxf + ifcopenshell (DXF/IFC floor plans)
uv sync --extra agents        # neuro-san (multi-agent orchestration)
```

## Quickstart — generate a building

Run the full spine (generate → validate → build → export) for a seed. Produces a 3D
model (`.glb`), a bill of materials (`.bom.json`), a floor plan (`.plan.svg`), and the
spec (`.spec.json`) in the output directory, and prints a summary.

```bash
ncad --seed 42 --rooms 4 --width 12 --depth 9   # writes artifacts into ./out
nv out                                           # then view them in the browser
```

Tests run fast by default; the geometry-kernel (OCP) tests are marked `slow`:

```bash
uv run pytest -m "not slow"   # fast suite (no OCP import)
uv run pytest -m slow         # kernel + end-to-end (real build123d geometry)
```

## Browser 3D viewer

View exported glTF/GLB models in any browser — no CAD or GL software needed. The `nv`
command (alias for `python -m ncad.viewer`) serves a polished Three.js viewer with
solid / material / wireframe / x-ray modes, edge overlay, grid, and orbit controls.

```bash
nv                 # serve models in ./out at http://127.0.0.1:8000
nv out --port 8777 # explicit directory and port
```

## Status

**v1 spine complete (Phase 5 gate passed):** `generate → validate → build → export`
runs end to end via `ncad`, producing model + BOM + plan + spec, with a browser viewer
(`nv`). See [`plan.md`](./plan.md) for the live tracker; Phase 6+ adds breadth (more
roof/footprint types, CAD interchange, the agent layer).
