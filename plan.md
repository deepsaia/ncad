# ncad — Implementation Plan & Tracker

Phased build order with progress tracking. The design rationale lives in
[`design.md`](./design.md); this file is *what to build, in what order, and what's done*.

**Legend:** `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

**Guiding rule:** prove the **spine end-to-end first** (Phase 0–4), then add breadth.
Each phase should leave `generate → build → render → BOM` in a working state.

---

## Status at a glance

| Phase | Title | Status |
|-------|-------|--------|
| 0 | Project bootstrap & dependency proof | `[x]` |
| 1 | Spec layer (schema + load/validate) | `[x]` |
| 2 | Generator (room-centric, v1 box) | `[ ]` |
| 3 | Builder + kernel (build123d) | `[ ]` |
| 4 | BOM + validators + export + plan render | `[ ]` |
| 5 | **v1 spine complete** (milestone gate) | `[ ]` |
| 6 | Breadth: roofs, footprints, openings | `[ ]` |
| 7 | Floor plans & CAD interchange — forward (`spec → DXF/IFC`) | `[ ]` |
| 8 | Agent interface (sessions + typed mutations) | `[ ]` |
| 9 | Multi-agent system (neuro-san) | `[ ]` |
| 10 | Render tiers & vision feedback loop | `[ ]` |
| 11 | Floor plan ingest — reverse (`DXF/IFC → spec`) | `[ ]` |
| 12 | Beauty render (Blender) — deferred | `[ ]` |
| 13 | General objects & scenes — future | `[ ]` |

---

## Phase 0 — Project bootstrap & dependency proof

Goal: a working, importable environment and a proven kernel before any modeling code.

- [x] `uv` venv pinned to Python 3.13 (`.python-version` = `3.13`)
- [x] `pyproject.toml` with project metadata and v1 deps
  - [x] core: `build123d`, `jsonschema`, `leaf-common` (IO/HOCON; pulls `pyhocon`), `numpy`, `trimesh`, `pyrender`
  - [x] (later, optional-group) interchange: `ezdxf`, `ifcopenshell`; agents: `neuro-san`
- [x] `uv sync` / lockfile committed (`uv.lock`, 335K)
- [x] **Import smoke test** — `build123d`, `OCP`, `trimesh`, `leaf_common` import without
      error (8 tests pass; confirms the native OCP binding *loads* on 3.13, not just resolves)
- [x] Repo layout scaffolded: `src/ncad/{spec,generate,build,kernel,bom,validate,render,export}/`,
      `schema/`, `tests/`, `examples/`
- [x] `pytest` runs (8 passed)
- [x] `.gitignore`, README pointer to `design.md` / `plan.md`
- [x] Decide & document: lint/format = **ruff** (E/F/I/UP/N, line 100); tests under `tests/`

> **Note (for Phase 3):** first `import OCP`/`build123d` costs ~90s (large native
> extension). Keep heavy-kernel tests separate from fast spec/validator/BOM tests so the
> quick feedback loop stays quick (e.g. a `kernel`/`slow` pytest marker).

## Phase 1 — Spec layer

Goal: a validatable spec contract; load/serialize from HOCON & JSON to a plain dict.

- [x] `schema/building_schema.hocon` — schema v1 in HOCON (storeys, walls, openings, rooms, roof); JSON-Schema vocabulary, DRY via `${definitions.x}`, no `$`-keys
  - [x] `schema_version`, `seed`, `units`, Z-up/origin conventions encoded/documented
  - [x] stable `id` required on every entity
  - [x] openings parameterized by `along` (0..1), not world coords
  - [x] **permissive by design** — no `additionalProperties=false`; schema evolves over time, tighten later w/ `schema_version` bumps
- [x] `SpecLoader` — HOCON and JSON → dict via `leaf-common`; dispatch by extension
- [x] `SchemaValidator` + `SchemaIssue` — `jsonschema` (draft 2020-12) on the loaded dict; returns structured issues (data, not raised)
- [x] `SpecWriter` — serialize dict back to HOCON/JSON via `leaf-common`
- [x] Fixture spec: `tests/fixtures/box_house.hocon` (hand-authored boring box; comments + shared-value ref)
- [x] Tests (TDD, 16 passing): load JSON/HOCON, substitutions, schema valid/invalid cases, round-trip, example validates

> **Note:** schema is authored in HOCON, not JSON — `jsonschema` validates a *dict*, so
> the on-disk format is ours; HOCON gives comments + `${...}` DRY. No `$`-keys (HOCON's
> `$` sigil mangles them). Whole pipeline is HOCON; no JSON round trip.

## Phase 2 — Generator (room-centric, v1 box)

Goal: `generate(seed, params) → spec`, fully seeded & reproducible.

- [ ] `generate(seed, params)` entry point; all randomness seeded here
- [ ] Footprint: single rectangle from params
- [ ] BSP room subdivision targeting per-room areas (seeded)
- [ ] Emit walls from room boundaries; **dedupe shared edges**
- [ ] Place doors on shared edges; windows on exterior walls by spacing rule
- [ ] Flat roof from footprint
- [ ] Tests: same `(seed, params)` → byte-identical spec (golden spec)

## Phase 3 — Builder + kernel

Goal: pure `build(spec) → geometry` on the build123d backend.

- [ ] `Kernel` interface (swappable backend contract)
- [ ] `build123d` kernel implementation
- [ ] Walls = extruded boxes from centerlines; `union` for visual solid
- [ ] Openings = boolean subtraction
- [ ] Flat roof via `roof_builders["flat"]` (registry dispatch from the start)
- [ ] Floor slab
- [ ] `build(spec)` is pure — no randomness, no global state (assert in tests)
- [ ] Tests: golden spec → geometry hash stable across runs

## Phase 4 — BOM + validators + export + plan render

Goal: the three outputs that make the spine real.

- [ ] **BOM** — `quantities(spec)` traversal: wall volume/area (minus openings),
      door/window counts by type/size, slab area, roof area. **From spec, not mesh.**
  - [ ] Golden BOM test
- [ ] **Validators** — geometric, topological, architectural-sanity passes returning
      structured issues tagged with `id`s
  - [ ] Tests: known-bad specs produce expected issues
- [ ] **Export** — glTF (render) + STEP (CAD) writers
- [ ] **Plan render** — top-down plan straight from spec (matplotlib/SVG), colored by
      semantic type, with `id` labels
  - [ ] Golden plan image test

## Phase 5 — v1 spine complete (milestone gate)

- [ ] End-to-end: `generate → build → glTF + plan render + BOM + validators` for the box
- [ ] One documented `examples/` run produces all artifacts
- [ ] README quickstart reproduces it
- [ ] ✅ **Gate:** spine works before any Phase 6+ breadth work begins

---

## Phase 6 — Breadth (additive, post-spine)

- [ ] Roofs: `shed`, `gable` (registry functions); `hip` via straight skeleton
- [ ] Footprints: union of rectangles → L/T/U shapes
- [ ] Opening placement rules; multi-storey support
- [ ] Orthographic elevations + isometric views (legible-to-model styling)
- [ ] Materials (post-export)

## Phase 7 — Floor plans & CAD interchange (forward: `spec → DXF/IFC`)

Goal: a derived, editable floor plan an architect/SME can open in AutoCAD/FreeCAD. A
projection of the canonical spec, **not** a second source of truth. Distinct from the
Phase-4 plan *render* (raster, for the vision model) — this is real-coordinate vector.

- [ ] `floorplan` unit; reads spec, parallel to glTF/STEP writers (no builder/kernel touch)
- [ ] **DXF writer** (`ezdxf`) on standard layers (`A-WALL`, `A-DOOR`, `A-GLAZ`,
      `A-ANNO-DIMS`, `A-ANNO-TEXT`)
  - [ ] dimension lines, room labels + areas, door swings, north arrow, title block
  - [ ] round-trip sanity: open emitted DXF in FreeCAD without errors
- [ ] **IFC writer** (`ifcopenshell`) — walls/doors/windows/spaces as objects + quantities
      (reuses BOM semantics from Phase 4)
- [ ] Optional **SVG/PDF** printable plan
- [ ] Tests: golden DXF (layer + entity counts), golden IFC entity set

## Phase 8 — Agent interface (sessions + typed mutations)

- [ ] Session store (holds a spec)
- [ ] Typed mutation set (`set <id>.<field>`, `add_door`, …) as dict patches
- [ ] Mutations validated against schema + validators **before apply**
- [ ] HTTP surface (`/sessions`, `/edit`, `/validate`, `/bom`, `/render`, `/export`)
- [ ] Free-form Python escape hatch (documented, secondary)
- [ ] Mutations exposed as agent tool definitions

## Phase 9 — Multi-agent system (neuro-san)

Goal: orchestrate *which* mutations to apply and *when*, on top of the Phase-8 API.
Agents are clients of the mutation surface, not a replacement for it.

- [ ] neuro-san added; wire spec/mutation/validate/bom/render as `coded_tools` / MCP tools
- [ ] Declarative HOCON agent network (e.g. planner / editor / BOM-checker / critique)
- [ ] Agents drive sessions through the typed mutation API only (constrained action space)
- [ ] End-to-end: prompt → agent network → valid spec → artifacts

## Phase 10 — Render tiers & vision feedback loop

- [ ] `Renderer` interface + fast headless backend (`pyrender`)
- [ ] Annotated renders (dimension lines, room labels, north arrow, scale bar, ids)
- [ ] Render cache keyed by `hash(spec) + view`
- [ ] Loop: build → validators → render → vision critique → structured edits → rebuild
- [ ] Iteration cap + convergence tracking

## Phase 11 — Floor plan ingest (reverse: `DXF/IFC → spec`)

Goal: consume an external floor plan and reconstruct a canonical spec. The inverse,
genuinely hard problem (same wall→room reconstruction as §2, on raw CAD primitives).

- [ ] IFC ingest first (carries semantic objects — the easier path)
- [ ] DXF ingest: layer interpretation → wall centerlines → endpoint snap → junctions →
      planar-face room detection → door/window block classification → fit to schema
- [ ] Reconstruction reuses the Phase-4 validators; flags low-confidence results for review
- [ ] Human-in-the-loop confirmation for ambiguous reconstructions
- [ ] Tests: round-trip a Phase-7-emitted DXF/IFC back to a spec; compare to original

## Phase 12 — Beauty render (Blender) — deferred

- [ ] Blender backend behind `Renderer` interface, consuming **exported glTF only**
- [ ] Decide in-process (`bpy`) vs out-of-process (`blender --background --python`)
- [ ] Cycles/EEVEE beauty stills from fixed cameras

## Phase 13 — General objects & scenes — future

- [ ] Generalize beyond buildings: props, furniture, terrain, scene layout
- [ ] Shared kernel/render/export layer with the architecture engine
- [ ] IFC/BIM export (BOM already provides the semantic quantities)

---

## Open questions / decisions log

- [x] Lint/format toolchain — **ruff** (resolved Phase 0): `select = E, F, I, UP, N`, line length 100.
- [x] HOCON authoring — **resolved Phase 1: HOCON from the start**, for both specs and the schema itself (JSON still loads as a superset).
- [ ] When typed mutations land (Phase 8), do we keep specs immutable + return new spec, or mutate in place per session?
- [ ] Vision model provider/client for Phase 10.
- [ ] Floor plan forward (Phase 7): DXF + IFC both in first cut, or DXF first since it's the most common architect interchange?
- [ ] DXF layer naming — adopt the AIA/NCS `A-WALL` convention as written, or a simpler custom scheme?
- [ ] Ingest (Phase 11): how much human-in-the-loop is acceptable vs. fully automatic reconstruction?
