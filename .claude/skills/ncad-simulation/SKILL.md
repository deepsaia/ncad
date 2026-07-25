---
name: ncad-simulation
description: >-
  Export ncad assemblies as robots (URDF/MJCF/SDF), run structural FEA load cases, and generate
  standard parts. Use when the user wants a robot description with computed inertials, a stress or
  modal or thermal analysis, or a standard fastener/pipe/flange/bearing/profile. For plain parts,
  assemblies, or motion studies, use the ncad-authoring skill instead.
---

# ncad simulation and standard parts

The advanced downstream of ncad: turn an assembly into a simulation-ready robot, run a finite-element
load case, or generate a catalog-standard part. This skill covers the three simulation-adjacent kinds.

## When to use

- **Export a robot** from an assembly + a physics overlay (URDF / MJCF / SDF, with inertials computed
  from the geometry) -> `reference/robots.md`.
- **Run an FEA load case** (static stress, modes, thermal) on a part -> `reference/analyses.md`.
- **Generate a standard part** (fastener, pipe, flange, bearing, profile) -> `reference/standard-parts.md`.

For plain parts, assemblies, or motion studies, use the **ncad-authoring** skill instead.

## The workflow

1. **Identify the intent** (robot / analysis / standard part).
2. **Author the overlay** (physics or analysis) or **choose the family + designation** (standard
   part), using the matching `reference/<kind>.md`. Overlays reference an existing assembly or part
   built with ncad-authoring.
3. **Run the command** (table below).
4. **Read and report the real result** honestly: inertia is COMPUTED (never authored); FEA and CAM
   delegate to external tools (CalculiX `ccx`, a slicer) that may not be installed. When a delegated
   solver is absent, the command reports a `skipped` status and the document still validates. Report
   that status truthfully; never fake a solve result.

## Intents and commands

| Intent | Document | Command | Reference |
| --- | --- | --- | --- |
| export a robot | `.physics.hocon` | `ncad physics <doc>` | `reference/robots.md` |
| run an FEA load case | `.analysis.hocon` | `ncad analyze <doc>` | `reference/analyses.md` |
| generate a standard part | (none) | `ncad spgen <family> <designation>` | `reference/standard-parts.md` |

`ncad physics --sweeps` also precomputes per-joint articulation for the viewer. FEA needs the `fea`
extra (`uv sync --extra fea`) for meshing, plus a `ccx` binary (or `NCAD_CCX`) for the solve.

## Principles

- **Inertia is derived, not typed.** A physics overlay supplies only actuation; mass, center of mass,
  and the inertia tensor come from the solids and their materials.
- **Delegate, do not fake.** CalculiX and slicers are external and optional; report `skipped`
  honestly when they are absent.
- **Accurate vocabulary.** Every export format, procedure, load type, and standard family named here
  matches the live engine.

Deep reference: the live docs guides at
https://deepsaia.github.io/ncad/ncad/guides/authoring-robots/ (and authoring-analyses / standard-parts).
