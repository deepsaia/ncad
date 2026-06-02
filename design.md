# ncad — Design Document

**Prompt → 3D models.** An agent, given a natural-language prompt and access to a
parametric modeling toolkit, writes/edits a structured model and renders it out to
3D objects, scenes, and architecture (buildings, houses, industrial structures).

This document is the validated design. It describes *what* the system is and *why*
it is shaped this way. The phased build order and progress tracking live in
[`plan.md`](./plan.md). Background reasoning and the original critique that this
design distills live in [`docs/design_ideas.md`](./docs/design_ideas.md).

---

## 0. Scope and first principles

**Architecture-first.** The first real version targets *buildings* (footprint →
rooms → walls → openings → roof → BOM → render). General objects and scenes are a
later, additive layer — not v1. This focus is deliberate: architecture is the domain
where a declarative spec, deterministic builder, and traversal-based bill-of-materials
pay off most, and proving that spine makes every later feature an additive change to
one layer rather than a rewrite.

**The one decision that shapes everything: separate the *spec* from the *geometry*.**
The system is three layers with strictly one-way data flow:

```
   params + seed                spec (dict)                geometry
        │                            │                         │
        ▼                            ▼                         ▼
  ┌───────────┐   spec   ┌────────────────────┐  geom  ┌──────────────┐
  │ generator │ ───────► │  builder (pure fn) │ ─────► │ render /     │
  │ (random)  │          │  spec → geometry   │        │ export / BOM │
  └───────────┘          └────────────────────┘        └──────────────┘
        ▲                            ▲
        │                            │
   all randomness            no randomness,
   lives here                no global state
```

- **Spec** — structured, validatable data. The single source of truth.
- **Builder** — a *pure* function `build(spec) → geometry`. Same spec → identical
  geometry, always.
- **Generator** — `generate(seed, params) → spec`. *All* randomness is isolated here.

Why this matters for every goal of the project:

- **Agents** edit a small, validatable data structure, not free-form geometry code.
  The action space is constrained, so far fewer invalid states.
- **BOM** falls out of the spec by traversal — every wall's volume and every door's
  type is already known. Quantities are never reverse-engineered from a mesh.
- **The feedback loop** edits the spec and re-runs the builder, instead of patching
  geometry in place.
- **Reproducibility & testing** — specs are JSON you can snapshot, diff, and
  golden-test; geometry can be hashed.

**Corollary: don't model "just meshes" internally, even though the output is meshes.**
Keep a *semantic model* — walls, openings, storeys, roof as first-class entities.
Meshes are an *output* of that model. This is what makes the result architecture
rather than extruded blobs, and it is the straight path to IFC/BIM later.

### Cross-cutting conventions (fixed on day one)

- **Units:** meters. **Up axis:** Z-up. **Origin:** documented, world origin at the
  footprint's reference corner.
- **Schema versioning:** every spec carries `schema_version` (int). Specs are
  persisted, so migrations will be needed.
- **Determinism:** the builder is pure. The generator is seeded; `seed` is part of
  the spec.

---

## 1. The spec layer

The spec is a plain Python **`dict`**, authored in **HOCON** (JSON also loads, since
HOCON is a JSON superset), governed by a single schema at `schema/building_schema.hocon`.
We deliberately do **not** use Pydantic classes in v1 — the value of the spec is that it
is *validatable*, and the JSON-Schema *vocabulary* (draft 2020-12) + the `jsonschema`
library delivers that without class boilerplate.

**The schema is itself authored in HOCON.** `jsonschema` validates a *dict*, never a
file, so the schema's on-disk format is ours to choose — and HOCON wins for the same
reasons specs do: inline comments, and DRY via HOCON `${...}` substitution (shared
`definitions` inlined at load time) instead of JSON-Schema `$ref`. We avoid all
`$`-prefixed keys (`$schema`/`$id`/`$ref`/`$defs`) because HOCON's `$` substitution
sigil mangles them; the draft is passed to the validator explicitly instead. Everything
in the pipeline is HOCON; there is no JSON-vs-HOCON round trip.

**Library: `leaf-common` for IO/persistence.** We do not hand-roll HOCON/JSON loading.
The `spec` unit wraps `leaf-common`'s `EasyHoconPersistence` / `EasyJsonPersistence`
(both return plain dicts — a direct fit for the dict spec), and layers `jsonschema`
validation on top. The schema itself loads through the same `leaf-common` HOCON path.
`leaf-common` is mature and shares the LEAF ecosystem with our agent framework
(`neuro-san`, §6), keeping the spec and agent layers consistent. (`dspu` was evaluated
but is too early — `0.0.4` — to depend on for foundational persistence.)

> If typed access becomes painful later, classes can be layered on *over* the dict
> without changing the on-disk contract. The schema is the contract; classes would be
> a convenience.

### Shape of a building spec

```jsonc
{
  "schema_version": 1,
  "seed": 42,
  "units": "m",
  "storeys": [
    {
      "elevation": 0.0,          // z of finished floor
      "height": 3.0,             // floor-to-floor
      "walls": [
        {
          "id": "wall_0",
          "start": [0.0, 0.0],   // centerline start (x, y)
          "end":   [6.0, 0.0],   // centerline end
          "thickness": 0.2,
          "height": null,        // null → inherit storey height
          "openings": [
            {
              "id": "window_3",
              "kind": "window",  // "door" | "window"
              "along": 0.5,      // 0..1 position along the wall centerline
              "width": 1.2,
              "height": 1.4,
              "sill": 0.9        // 0 for doors
            }
          ]
        }
      ],
      "rooms": [
        { "id": "room_2", "polygon": [[0,0],[6,0],[6,4],[0,4]] }
      ]
    }
  ],
  "roof": { "kind": "flat", "thickness": 0.2 }
}
```

**Two invariants that pay off later:**

1. **Stable `id` on every entity.** The agent and the feedback loop say *"widen
   `window_3`"* rather than re-emitting everything.
2. **Openings belong to walls**, parameterized by `along` (0..1) on the centerline —
   *not* world coordinates. They move automatically when the wall moves. Storing world
   coordinates desyncs the moment anything shifts.

---

## 2. The generator — room-centric, layout-graph → geometry

The generator is seeded and reproducible: `generate(seed, params) → spec`.

We choose **room-centric** generation over wall-centric. (See
[`docs/design_ideas.md` §2](./docs/design_ideas.md) for the full trade-off.) In short:

- **Wall-centric** places walls and lets rooms *emerge* as enclosed faces. Flexible,
  but to know "what rooms exist" — needed for BOM, door placement, and validation —
  you must run planar-graph face detection plus solve wall junctions (mitering,
  T-intersections). Junctions are the classic time-sink.
- **Room-centric** generates *rooms* first, then derives walls on their boundaries,
  deduplicating shared edges. Every room is enclosed by construction; BOM-per-room is
  trivial; doors go on shared edges, windows on exterior edges.

**v1 generation pipeline:**

1. Pick a footprint — v1: a single rectangle. (Later: union of rectangles → L/T/U.)
2. Subdivide into rooms — **binary space partitioning (BSP)** targeting per-room
   areas. Seeded, reproducible.
3. Emit walls from room boundaries; dedupe shared edges into single walls.
4. Place openings — a door on each shared edge (rooms reachable), windows on exterior
   walls by a spacing rule.
5. Roof — v1: flat.

The schema can still *represent* freeform wall-centric specs; the generator just does
not start there.

---

## 3. The builder and the geometry kernel

`build(spec) → geometry` is a **pure function**. The geometry kernel sits behind a thin
`Kernel` interface so it is swappable.

**v1 kernel: `build123d` (OpenCASCADE / OCP under the hood).** Chosen for precise
dimensions, boolean subtraction for door/window openings, and clean export to **STEP**
(CAD-accurate) *and* mesh formats (**glTF/STL**) for rendering. Verified to resolve on
the target Python (see §7).

**Construction approach:**

- Each wall is an extruded box from its centerline.
- `union` the wall boxes for the *visual* solid — the union cleans up corners
  automatically.
- Openings are **boolean subtraction** of opening volumes from the wall solid.

**Wall junctions — the explicit trap:** do **not** try to make the *geometry* exact for
BOM. Build and union for looks; compute the **BOM from the parametric values, not the
unioned mesh** (see §4). Trying to measure "how much wall remains after a corner
overlap" from geometry is a rabbit hole; `length × thickness × height` minus opening
volumes is exact and trivial. **Decouple pretty geometry from accurate quantities.**

**Roofs as a registry.** `roof_builders[roof.kind]` dispatches to a per-kind function.
v1 ships `flat`; `shed` and `gable` are straightforward additions; `hip` over arbitrary
footprints uses the **straight skeleton** when needed. Adding a roof type is a new
function, not a new branch everywhere.

---

## 4. Bill of materials — a traversal, and free validation

Because the semantic model knows every entity and its dimensions, the BOM is a `sum`/
`count` over the spec — **never measured from the mesh**:

- wall volume and face area per wall (minus opening volumes),
- doors and windows counted by type and size,
- floor slab area, roof area by pitch.

Each entity type gets a `quantities()` contribution; results fold up. Two bonuses: the
BOM doubles as a cheap regression check (did an edit unexpectedly triple the glazing
area?), and it is the natural seed for an IFC export later — IFC wants exactly these
semantic quantities.

---

## 5. Validators — cheap, deterministic, text-returning

Most defects in generated geometry are *detectable without a vision model*, and those
checks are essentially free. A validator pass runs over the spec + semantic model and
returns **structured issues** (each tagged with the offending `id`s) as text:

- **Geometric:** footprint closed and non-self-intersecting; each opening fits within
  its wall (`along·length ± width/2` in bounds, `sill + height ≤ wall height`);
  openings on the same wall don't overlap; roof covers the plan.
- **Topological:** walls form closed loops around each room; every room reachable
  through doors (connectivity on the room graph); no orphaned walls.
- **Architectural sanity:** min room area, min ceiling height, door width ≥ threshold.

This catches the overwhelming majority of "broken building" cases deterministically,
cheaply, and reproducibly. The vision model is reserved for what validators *cannot*
judge (§7).

---

## 6. The agent interface (designed now, built after the spine)

**Multi-agent framework: `neuro-san`.** When we build the multi-agent system, we use
neuro-san — a data-driven agent orchestration framework. Agents are written in
declarative **HOCON** files (a pleasing symmetry with our HOCON-authored specs), and it
brings `coded_tools`, a toolbox, and MCP tools, which makes standing up multi-agent
systems fast. Crucially, this slots *on top of* the typed-mutation API below: agents are
clients of the session/mutation surface, not a replacement for it. The mutations remain
the validated, constrained action space; neuro-san orchestrates *which* mutations to
apply and *when* (e.g. a planner agent, a critique agent, a BOM-checker agent).
Verified to resolve on 3.13.13.

### The session and mutation surface

A **session** holds a spec; everything operates on the session.

**Primary interface: typed mutations.** The agent calls constrained, validated tools —
e.g. `set window_3.width 1.2`, `add_door room_2 room_3` — expressed as dict patches
against the spec. Every mutation is **validated against the schema and the validators
before being applied**. The constrained action space is what keeps the agent out of
invalid states; it is the same reason the spec is schema-governed. These granular
mutations *are* the agent's tool definitions.

**Escape hatch (secondary):** an "evaluate this Python against the model" path for power
users. Documented, but not the default route, and not part of v1.

**Provisional HTTP surface** (wired to agents later):

```
POST /sessions             {seed, params}      -> {session_id, spec}
GET  /sessions/{id}/spec                        -> spec
POST /sessions/{id}/edit   {mutations: [...]}   -> {spec, issues}
GET  /sessions/{id}/validate                    -> {issues: [...]}
GET  /sessions/{id}/bom                         -> {quantities}
GET  /sessions/{id}/render?view=plan|iso|...    -> image
POST /sessions/{id}/export {format}             -> file (glTF/STEP/DXF/IFC)
```

---

## 7. Rendering and the feedback loop (post-v1)

**Two render tiers, both behind a `Renderer` interface:**

1. **Fast, in-loop renderer** — for validation and vision critique. Export mesh →
   headless `pyrender`/`trimesh`; the plan view can be a 2D matplotlib/SVG drawing
   straight from the spec. This is the renderer used inside the iteration loop.
2. **Beauty render (deferred, post-v1)** — **Blender (Cycles/EEVEE)** for
   photorealistic stills. It is an *optional backend* behind the same `Renderer`
   interface, and it **consumes the exported glTF — it never imports the spec or the
   builder.** Because of that boundary, whether it runs *in-process* (`bpy`, available
   on Python 3.13) or *out-of-process* (`blender --background --python`) is purely an
   implementation detail of the backend. It is explicitly **not** part of v1.

**Renders made legible to a model** (different from making them pretty):

- A fixed set of **orthographic** views — top-down plan (the single most informative
  view), 2–3 elevations, one isometric — from a fixed camera per view, so frames are
  comparable across iterations.
- Flat-shade, **color by semantic type** (walls / doors / windows / roof) so the model
  can identify elements unambiguously.
- Overlay annotations: dimension lines, room labels, north arrow, scale bar, and entity
  `id`s. An annotated plan is dramatically more useful to a vision model than a bare
  render.

**The loop:** `build → validators (cheap, text) → if clean, render → vision critique
against the prompt`. Both kinds of feedback come back as **structured spec edits** (a
JSON patch / typed mutations), which are validated before applying → rebuild. Renders
are cached by `hash(spec) + view`. Iterations are capped and convergence tracked, so it
cannot loop forever.

---

## 8. Floor plans & CAD interchange (DXF / IFC)

A 2D **floor plan** is the lingua franca of architecture: it is what you hand to an
architect or SME, and what opens and edits cleanly in AutoCAD, FreeCAD, Revit, etc. We
make it a first-class artifact — *but as a projection of the spec, not a second source
of truth.* The spec stays canonical; the floor plan is derived from it the same way BOM
and renders are.

### Forward path (derived view — earlier): `spec → floor plan`

A deterministic projection of the spec to a **vector** floor plan, distinct from the
Phase-4 plan *render* (which is a raster/SVG made legible to a vision model). The CAD
floor plan is real-world-coordinate vector geometry with proper layers an architect can
edit:

- **DXF** via `ezdxf` — the practical AutoCAD/FreeCAD interchange format. Emit on
  standard layers (e.g. `A-WALL`, `A-DOOR`, `A-GLAZ`, `A-ANNO-DIMS`, `A-ANNO-TEXT`),
  with dimension lines, room labels/areas, door swings, a north arrow, and a title block.
- **IFC** via `ifcopenshell` — the *semantic* BIM interchange: walls, doors, windows,
  and spaces as first-class objects with their quantities. This is where the BOM (§4)
  pays its second dividend — IFC wants exactly those semantic quantities. Complements
  DXF (geometric/layered) with a true object model.
- Optionally a printable **SVG/PDF** plan for sharing without CAD software.

This is a clean addition: a new writer in the `export`/`floorplan` unit reading the spec,
parallel to the glTF/STEP writers. It does not touch the builder or kernel.

### Reverse path (ingest — later, genuinely hard): `floor plan → spec`

Consuming an external floor plan to *generate* an architecture model is the inverse
problem, and it is the same wall-centric→room-centric reconstruction challenge flagged
in §2 — only harder, because the input is raw CAD primitives, not our clean spec:

- Parse DXF (or IFC) → interpret layers → recover wall centerlines from line/polyline
  pairs → snap endpoints → solve junctions → detect enclosed faces as rooms → classify
  door/window blocks into openings → fit it all to the schema.
- IFC ingest is easier than DXF ingest (it already carries semantic objects); raw DXF
  ingest needs the most heuristics and human-in-the-loop confirmation.
- It gets its **own validation pass** (the §5 validators apply directly to the
  reconstructed spec) and should surface low-confidence reconstructions for review.

Because everything funnels back into the canonical **dict spec**, an ingested plan
immediately gains build, BOM, validation, render, and re-export for free.

### Boundary

`floor plan ⇄ spec` is symmetric around the spec, never a side-channel:

```
                    ┌──────────────────┐
   DXF / IFC  ──────►│                  │──────►  DXF / IFC / SVG / PDF
   (ingest, later)   │   dict  spec     │  (derived floor plan, earlier)
                    │  (canonical SOT) │
   params+seed ─────►│                  │──────►  glTF / STEP / IFC / BOM / render
   (generator)       └──────────────────┘
```

---

## 9. Environment and dependencies

- **Python 3.13** (`.venv` pinned via `uv`; `.python-version` = `3.13`). 3.13 is chosen
  over 3.14 specifically so that `bpy` (Blender, cp313-only wheel) remains an
  installable in-process option for the deferred beauty renderer. Adopting `bpy` as a
  hard dependency would pin the project to 3.13 until Blender ships a cp314 wheel.
- **Verified to co-resolve on 3.13.13:** `build123d` (+ `cadquery-ocp`), `trimesh`,
  `manifold3d`, `pyrender`, `numpy`, `bpy`. (Resolution proves a compatible wheel
  exists; first plan task verifies *import*.)
- **Core deps (v1):** `build123d`, `jsonschema`, `leaf-common` (IO/HOCON/JSON
  persistence; pulls `pyhocon`), `numpy`, `trimesh`, `pyrender` (or matplotlib for the
  plan view).
- **Interchange deps (post-spine):** `ezdxf` (DXF floor plans), `ifcopenshell` (IFC/BIM).
  Both verified to resolve on 3.13.13.
- **Agent deps (post-spine):** `neuro-san` (multi-agent orchestration; declarative HOCON
  agents — verified to resolve on 3.13.13), a vision model client (critique loop), an
  HTTP framework if the API is exposed over the network.
- **Deferred deps:** `bpy`/Blender (beauty render).

---

## 10. Component boundaries (each unit, one purpose)

| Unit | What it does | Depends on |
|------|--------------|------------|
| `schema/` | spec contract (`building_schema.hocon`, JSON-Schema vocabulary) | — |
| `spec` | load/validate/serialize specs (JSON/HOCON ↔ dict) | schema, jsonschema, leaf-common |
| `generate` | `generate(seed, params) → spec` (all randomness) | spec |
| `kernel` | swappable geometry backend interface + build123d impl | build123d |
| `build` | pure `build(spec) → geometry` | spec, kernel |
| `bom` | `quantities(spec) → BOM` (traversal only) | spec |
| `validate` | spec → structured issues (text) | spec |
| `render` | `Renderer` interface + fast backend; beauty backend deferred | build output |
| `export` | glTF / STEP writers | build output |
| `floorplan` *(post-spine)* | `spec → DXF/IFC/SVG` (forward); `DXF/IFC → spec` (ingest, later) | spec, ezdxf, ifcopenshell |
| `api` *(post-spine)* | sessions + typed mutations | all of the above |
| `agents` *(post-spine)* | neuro-san multi-agent orchestration over the API | api |

The test for these boundaries: can you understand what a unit does without reading its
internals, and change its internals without breaking consumers? Where the answer is no,
the boundary needs work.

---

## 10. First milestone (v1): prove the spine

Deliberately ignore most of the above and prove the spine end-to-end on the boring box:

> rectangular footprint → BSP into rooms → straight walls with box geometry → flat roof
> → doors on shared edges + windows on exterior walls → **glTF export + a plan render +
> a BOM + validators.**

No curves, no hip roofs, no materials, no agent loop, no vision. Once
`generate → build → render → BOM` works for the boring box, every listed feature
(curved walls, roof types, opening rules, the agent, the vision loop) is an additive
change to one layer rather than a rewrite.

Detailed, checkboxed build order and tracking: [`plan.md`](./plan.md).
