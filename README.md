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

Requires Python 3.13, managed via [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                 # install deps into .venv
uv run pytest -m "not slow"   # fast suite (no OCP import)
uv run pytest -m slow         # kernel + end-to-end (real build123d geometry)
```

## Quickstart

Build a feature-tree document to glTF, then view it in the browser:

```bash
ncad build examples/gate-0.1-first-shape/block.hocon   # writes out/block.glb
ncad                                                    # serve ./out at http://127.0.0.1:8000
```

`ncad` runs from any subdirectory of the project; the models directory defaults to
`<project-root>/out`.

## CLI

The `ncad` command (a typer app) is the single entrypoint:

- `ncad` or `ncad view [dir]`: launch the browser 3D viewer over a models directory.
- `ncad build <document> [--out DIR]`: build every part in a document to `<part>.glb`.

The viewer is also a local model-manager: pick an example spec from the searchable
tree, click Build to run it, and the model appears in the models list; each model has
hover actions to regenerate (rebuild from its recorded source) or delete it. The
sidebar is resizable (width persists). `ncad view` runs with hot-reload by default
(`--no-dev` to serve the cached page).

Viewer settings (display mode, material, lighting, scene toggles, reset, and the
BOM/Plan panels) live in a translucent floating controls panel over the viewport. It
uses icons by default (labels on hover, or toggle "show labels"), can be dragged and
snapped to any edge or anchored to a corner, and all its state persists across reloads.

## Examples and gates

Each roadmap gate has a self-contained example under `examples/gate-<id>-<name>/`. They
double as user-facing samples and as a regression net: every example is built and
checked by the test suite, so each gate stays a living, tested artifact.

- `examples/gate-0.1-first-shape/block.hocon`: a rectangle sketched on XY, extruded
  into a block. Proves the spine: document >> build >> glTF >> view.

## Status

**Phase 0 bucket 0.1 complete:** the general spine (feature-tree schema, op registry,
pure Builder, sketch + extrude ops, glTF export, viewer) builds a hand-authored
document and renders it. See [`docs/plan.md`](./docs/plan.md) for the live tracker.
