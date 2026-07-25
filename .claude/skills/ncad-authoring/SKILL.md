---
name: ncad-authoring
description: >-
  Author and build ncad parts, assemblies, and motion studies as text documents (HOCON). Use when the
  user wants to model a part (sketch, extrude, fillet, holes, patterns, direct edits), compose an
  assembly (instances, mates, joints, couplings), or drive a mechanism's motion. For robots/URDF,
  FEA, or standard fasteners/pipes/flanges, use the ncad-simulation skill instead.
---

# Authoring ncad documents

ncad turns a text document into exact-geometry CAD. You never hand-edit geometry: you write a
declarative document and a pure executor replays it. This skill covers the three everyday kinds.

## When to use

- **Model a part** (a single solid: sketch, extrude/revolve/loft/sweep, fillet/chamfer/shell/hole,
  patterns, booleans, direct edits) -> `reference/parts.md`.
- **Compose an assembly** (place instances, join with mates and lower-pair joints, add couplings)
  -> `reference/assemblies.md`.
- **Drive a mechanism** (sweep a joint over a range and solve the trajectory) -> `reference/motion.md`.

For robot export (URDF/MJCF/SDF), structural FEA, or generating standard parts, use the
**ncad-simulation** skill instead.

## The workflow

1. **Identify the document kind** (part / assembly / motion) from what the user wants.
2. **Author the HOCON** using the matching `reference/<kind>.md` for the exact vocabulary. Prefer
   trimming a real shipped example under `examples/` over writing from a blank page.
3. **Run the command** (table below).
4. **Read the diagnostics.** ALWAYS build or validate and report the real result; never claim
   success without running. `ncad validate <doc>` checks a document statically (no geometry) and
   exits non-zero if it is not ok; a build reports diagnostics as data.
5. **Iterate** on any reported issue (unknown reference, underconstrained sketch, DoF state, etc.).

## Document kinds and commands

| Intent | Document | Command | Reference |
| --- | --- | --- | --- |
| model a part | `.hocon` / `.json` | `ncad build <doc>` | `reference/parts.md` |
| compose an assembly | `.asm.hocon` | `ncad assemble <doc>` | `reference/assemblies.md` |
| drive a mechanism | `.motion.hocon` | `ncad motion <doc>` | `reference/motion.md` |
| check before building | any | `ncad validate <doc>` | - |
| view the result | (a built model dir) | `ncad view` | - |

`ncad build` accepts `--format glb,step,stl,...`; `ncad build/assemble/motion` accept `--out DIR`
(default `out/`). Artifacts land in `out/<kind>/<name>/`.

## Principles

- **Order is meaning.** A part is an ordered feature tree; each feature consumes the previous result.
  OpenCASCADE is order-sensitive, so a late shell or fillet can fail where a different order would
  not.
- **References survive rebuilds.** Pick edges/faces with selectors (`edges = vertical`,
  `select faces where type = 'cylinder'`), not raw indices, so an edit does not break a downstream
  feature.
- **Verify, do not assume.** Report what `ncad build` / `validate` actually returns.

Deep reference: the live docs guides at
https://deepsaia.github.io/ncad/ncad/guides/authoring-parts/ (and assemblies / motion).
