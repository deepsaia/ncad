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
| 2 | Generator (room-centric, v1 box) | `[x]` |
| 2.5 | Plan render (SVG, spec-only) — pulled forward | `[x]` |
| 3 | Builder + kernel (build123d) | `[x]` |
| 4 | BOM + validators + glTF export (plan render done in 2.5) | `[x]` |
| 4.5 | Browser 3D viewer (Three.js + stdlib server; BOM + plan panels, materials, lighting) | `[x]` |
| 5 | **v1 spine complete** (milestone gate) | `[x]` |
| 6 | Breadth: roofs (s1), L/T/U (s2), curved corners + irregular shapes (s2b) done; multi-storey deferred | `[~]` |
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

- [x] `Generator(params).generate(seed)` entry point; all randomness in one seeded `random.Random`
- [x] Footprint: single rectangle from params (`Rectangle` value type)
- [x] BSP room subdivision targeting balanced areas, seeded (`BspSubdivider`, largest-first, longer-axis, jittered, respects `min_room_size`)
- [x] Emit walls: 4 exterior (footprint edges) + interior from split segments — **dedup-free** (each split = exactly one wall; N rooms ⇒ N−1 interior walls)
- [x] Place doors on interior walls (spanning-tree reachability) + front door; windows on exterior by spacing (`OpeningPlacer`)
- [x] Flat roof from footprint
- [x] Tests (TDD, 32 passing): generated spec is schema-valid; same `(seed,params)` → identical; golden-spec fixture pins exact output; unique ids; counts

> **Note:** room-centric without geometric dedup — tracking the BSP split segment yields
> the interior wall directly, sidestepping the T-junction dedup problem design.md §2 warns
> about.

## Phase 2.5 — Plan render (pulled forward from Phase 4)

Goal: see the generated spec as a real image, with no geometry kernel. Pulled forward
for fast visual feedback once the generator existed.

- [x] `PlanTransform` — world (m, Y-up) → SVG (px, Y-down), uniform scale + margin (TDD, 5 tests)
- [x] `PlanRenderer` — spec → SVG: rooms, thickness-scaled walls, doors (red) / windows (blue) by type, room-id labels, title (TDD, 5 tests)
- [x] SVG chosen over matplotlib: vector, deterministic (golden-testable), zero new deps (`svgwrite` already present), legible-by-structure for tests
- [x] Verified visually: `out/box_house_seed42.svg` (rasterized via macOS `qlmanage`)

> **Deferred to Phase 4 polish:** punch real gaps in walls for openings (currently drawn
> as colored overlays centered on the wall line); dimension lines, north arrow, scale bar.

## Phase 3 — Builder + kernel

Goal: pure `build(spec) → geometry` on the build123d backend.

- [x] `Kernel` interface (swappable backend contract) — opaque solid handles; `box/union/subtract/volume/bounding_box/export`
- [x] `Build123dKernel` implementation (OCP); exports glTF/STEP/STL in **meters** (`Unit.M` — build123d defaults to mm)
- [x] Walls = axis-aligned extruded boxes from centerlines; `union` for visual solid
- [x] Openings = boolean subtraction (cut box overshoots wall faces for a clean through-cut)
- [x] Flat roof via `ROOF_BUILDERS["flat"]` registry (dispatch from the start)
- [x] Floor slab under the storey
- [x] `Builder(kernel).build(spec)` is pure — verified: same spec → same volume + bbox
- [x] Tests: fast builder logic vs a **FakeKernel** (no OCP); slow `build123d` geometry + export behind `-m slow`
- [x] Verified visually: built box_house seed 42 → glTF/STEP/STL; dims exactly match spec (12×9×3.2m)

> **Test split:** `FakeKernel` (sampling-based, dependency-free) lets all builder logic
> run in the **fast** suite (1.3s, OCP-free); only real geometry/export is `slow` (~90s
> cold OCP import). Run fast with `-m "not slow"`, kernel with `-m slow`.
>
> **v1 limitation:** builder assumes **axis-aligned walls** (raises otherwise). Rotated/
> angled walls are a Phase 6 extension (needs the rotated-box placement path).

## Phase 4 — BOM + validators + export + plan render

Goal: the three outputs that make the spine real.

- [ ] **BOM** — `quantities(spec)` traversal: wall volume/area (minus openings),
      door/window counts by type/size, slab area, roof area. **From spec, not mesh.**
  - [ ] Golden BOM test
- [x] **BOM** — `BomCalculator.quantities(spec)` traversal (`Bom` value type): wall volume/face area minus openings, door/window counts, floor area, roof area. **From spec, not mesh.** (TDD, 7 tests)
- [x] **Validators** — `SemanticValidator` over `GeometryValidator` (opening fit/overlap), `TopologyValidator` (room reachability via door graph), `ArchitecturalValidator` (min area/ceiling/door); structured `Issue`s tagged with ids (TDD, 8 tests)
  - [x] Known-bad specs produce expected issues; generated spec is clean (cross-check with generator)
- [x] **Export** — glTF/GLB + STEP + STL via the kernel (Phase 3); `.glb` is the self-contained default for the viewer
- [x] **Plan render** — done in Phase 2.5 (`PlanRenderer` → SVG)

> **Bug caught in real use:** text `.gltf` writes an external `.bin` buffer; the viewer
> 404'd on it. Fixed two ways — kernel now exports self-contained `.glb` (binary), and
> the server serves sidecar buffers too. Regression tests added.

## Phase 4.5 — Browser 3D viewer

Goal: view glTF/GLB models in any browser, no installs (machines without CAD/GL software).

- [x] `ModelCatalog` — lists/safely-resolves models + sidecars (`.bin`/`.bom.json`/`.plan.svg`); path-traversal rejected (TDD)
- [x] `ViewerServer` (+ handler) — stdlib `http.server`; routes `/`, `/api/models`, `/models/<name>`, `/api/bom/<model>`, `/api/plan/<model>`; correct MIME per ext (TDD integration)
- [x] `ArtifactExporter` — writes `<name>.glb` + `<name>.bom.json` + `<name>.plan.svg` sidecars (BOM/plan from spec, not mesh) (TDD)
- [x] `viewer_page` — polished Three.js SPA (CDN importmap, no npm): Solid/Material/Wireframe/X-ray modes; 16 material presets (swatches shown only in Material mode); lighting presets (sun/studio/spotlight/overcast); edges/grid/shadows/auto-rotate; orbit controls; ground shadow; live size/tri/mesh readout
- [x] Floating top-right panels: **BOM** + **Plan view**, each independently collapsible, state persisted in `localStorage`; fixed-width (no jitter); plan SVG scales via `viewBox`
- [x] `python -m ncad.viewer [dir] [--port]` launcher; **`nv` console-script alias**
- [x] Verified in a real browser (Playwright): renders, mode/material/light switching, panel collapse persistence; zero app console errors (only favicon 404)

## Phase 5 — v1 spine complete (milestone gate)

- [x] `Pipeline(kernel).run(seed, params, out_dir, name)` — generate → schema-validate (raises on contract failure) → semantic-validate (collects issues) → persist spec → build + export (`ArtifactExporter`); returns `PipelineResult` (TDD vs FakeKernel, 5 tests)
- [x] End-to-end with the **real** build123d kernel produces `.glb`/`.bom.json`/`.plan.svg`/`.spec.json`, clean schema + semantic, `glTF` magic bytes verified (slow test)
- [x] `ncad` console command (`python -m ncad.pipeline --seed N …`) prints artifacts + BOM + issues; `nv` to view
- [x] README quickstart reproduces it
- [x] ✅ **Gate passed:** the whole spine composes into one pipeline with no glue surprises; safe to start Phase 6 breadth

> **Surfaced by the gate (Phase 6 backlog):** seed 7 produced an `opening_overlap`
> between the front door and the first south-wall window — the `OpeningPlacer` window
> spacing doesn't reserve the door's footprint. The pipeline correctly *reported* it
> (issues are data, not a crash). Fix when revisiting opening placement.

---

## Phase 6 — Breadth (additive, post-spine)

**Slice 1 — pitched roofs + opening fix (done):**
- [x] Kernel gains a `prism` primitive (vertical profile extruded along a horizontal axis); implemented in `Build123dKernel` (real extrude) + `FakeKernel` (sampled). Additive — `box/union/subtract/flat` untouched.
- [x] Roofs: `shed`, `gable` via `ROOF_BUILDERS` registry + `kernel.prism`; optional `pitch`/`ridge_axis` defaulted; **schema** `enum` → `[flat, shed, gable]`, with `pitch`/`ridge_axis` properties (additive, old flat specs still valid)
- [x] Opening placement: front door no longer overlaps the first window (`OpeningPlacer` drops windows whose span hits the door). Seed 7 now validates clean; **seed-42 golden unchanged** (targeted fix, no breakage)
- [x] Viewer: query-string routing fix; demos regenerated via `ArtifactExporter` so BOM + plan sidecars populate for pitched-roof models
- [x] Verified in browser: gable house renders, BOM + plan panels populate (119 tests: 109 fast + 10 slow)

**Slice 2 — L/T/U footprints, straight corners (done):**
- [x] Kernel gains `extrude_polygon` (horizontal polygon → vertical prism), distinct from `prism`; `Build123dKernel` (Face/Wire/extrude up) + `FakeKernel` (`_PolygonPrism`, point-in-polygon). Additive.
- [x] `footprint_grid.py`: occupancy grid + L/T/U masks → marching-squares boundary (directed-edge cancellation) → CCW polygon w/ colinear collapse; greedy rectangle wings. Pure/deterministic (no RNG → rect stream untouched).
- [x] Generator `footprint_shape` param (`rect` default = **frozen path**, golden byte-identical); `L/T/U` → polygon walls (longest edge first) + per-wing BSP rooms + door-bearing seam walls; emits optional `storeys[0].footprint`; raises on pitched roof over shaped footprint.
- [x] Builder: slab + flat roof use `extrude_polygon` when `footprint` present (notch genuinely empty), else frozen box/bounds path. Schema documents optional `footprint`.
- [x] **Specs from HOCON too:** hand-authored `tests/fixtures/L_house.hocon` + generator-exported `T_house.hocon`/`U_house.hocon`; all load + validate + build. New `golden_spec_L_seed42.json`.
- [x] Verified in browser (nv + Playwright): L and U render with empty notches, BOM + plan panels populate (145 tests: 132 fast + 13 slow)

**Slice 2b — curved/rounded corners + irregular shapes (done):**
- [x] Schema: footprint vertex is `oneOf [vec2, {point, corner_radius}]`; optional wall `arc` form (additive; plain specs + goldens stay valid)
- [x] Kernel `extrude_rounded_polygon` (fillet corners then extrude) + `arc_wall` (annular sector, **minor arc**); both backends (build123d true-arc, FakeKernel tessellated)
- [x] Builder: rounded slab/roof dispatch on `corner_radius`; straight-vs-arc wall dispatch; **oriented (any-angle) straight walls** via `extrude_polygon` rectangle (diagonal walls build, not just axis-aligned)
- [x] Generator `corner_radius` param (default 0 = frozen): rounds **both convex (CCW) and concave (CW)** corners, shortens adjacent walls to tangent points, inserts arc walls. rect+L goldens byte-identical.
- [x] BOM + geometry validator use **arc length** for arc walls
- [x] `LoopValidator`: exterior walls must close into a loop (angle-agnostic endpoint-degree check; interior `interior_*` walls excluded). Catches gaps in irregular outlines.
- [x] PlanRenderer draws arc walls as sampled curves (rounded corners look rounded in the plan)
- [x] **Irregular shapes:** hand-authored `tests/fixtures/irregular_house.hocon` — hexagon w/ diagonal straight walls + mix of sharp & rounded corners; loads, validates, builds, exports
- [x] Verified in browser (nv + Playwright): rounded L/T/U (both corner types correct) + irregular hexagon render and round-trip (174 tests: 154 fast + 20 slow)
- Bug found & fixed via visual review: arc band swept the **major** arc (inverted concave corners) — normalized to minor arc.

**Slice 3+ — deferred (higher risk, own slices):**
- [ ] Openings on diagonal/arc walls (currently only axis-aligned walls take openings)
- [ ] Generator-driven irregular shapes + per-corner radius mix (hand-authored works today)
- [ ] Multi-storey support (Builder currently builds `storeys[0]` only)
- [ ] `hip` roof via straight skeleton
- [ ] Orthographic elevations + isometric views (legible-to-model styling)
- [ ] Materials carried in the spec (post-export)

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
