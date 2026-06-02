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

## Browser 3D viewer

View exported glTF/GLB models in any browser — no CAD or GL software needed. The `nv`
command (alias for `python -m ncad.viewer`) serves a polished Three.js viewer with
solid / material / wireframe / x-ray modes, edge overlay, grid, and orbit controls.

```bash
nv                 # serve models in ./out at http://127.0.0.1:8000
nv out --port 8777 # explicit directory and port
```

## Status

Spine complete through Phase 4 (`generate → build → 3D/STEP + plan render + BOM +
validators`), plus a browser 3D viewer. See [`plan.md`](./plan.md) for the live tracker.
