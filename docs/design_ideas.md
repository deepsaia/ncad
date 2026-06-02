This is a fun system to design, and the pipeline you sketched (footprint → walls → roof → openings) is the right intuition. But before locking it in, I want to push on one architectural decision that will determine whether this scales to agents and BOM, or fights you forever.

## The one decision that matters most: separate the *spec* from the *geometry*

Your instinct ("create footprint, then extrude, then add roof…") describes an *imperative* pipeline — code that does things step by step. For an agent-driven, reproducible, BOM-capable system, you want a *declarative* core instead:

- A **building spec** — structured, typed data (the source of truth). "This building has 2 storeys; storey 0 has these walls with these centerlines, thicknesses, heights; these openings at these positions; a gable roof at 30°."
- A **deterministic builder** — a pure function that turns a spec into geometry. Same spec (+ seed) always produces identical geometry.
- A **stochastic generator** — turns `(seed, parameters, constraints)` into a spec. All randomness lives *here*, isolated from the builder.

Why this matters for everything you listed:
- **Agents** edit a small, validatable data structure, not free-form geometry code. The action space is constrained, so far fewer invalid states.
- **BOM** falls out of the spec/semantic model by traversal — you already know every wall's volume and every door's type. You never have to reverse-engineer quantities from a mesh.
- **The feedback loop** edits the spec and re-runs the builder, instead of patching geometry in place.
- **Reproducibility & testing**: specs are JSON you can snapshot, diff, and golden-test.

The corollary: **don't model "just meshes" internally, even though your output is meshes.** Keep a *semantic model* — walls, openings, storeys, roof as first-class typed objects. Meshes are an *output* of that model. This is what makes it architecture rather than extruded blobs, and it's a straight path to IFC/BIM later. Let me sketch the whole thing:Now let me sketch the architecture so we have something concrete to anchor the rest of the discussion:The teal box is the heart of it: everything reads from and writes to the spec, and the build is a one-way function down from it. Now the details.

## 1. Model the building semantically, not as a list of mesh ops

Your spec should describe *architecture*, not geometry operations. Something like (Pydantic v2 — gives you validation, JSON serialization, and JSON Schema for the agent for free):

```python
class BuildingSpec(BaseModel):
    seed: int
    schema_version: int = 1
    units: Literal["m"] = "m"          # pick meters, Z-up, fix the origin convention
    storeys: list[Storey]
    roof: Roof

class Storey(BaseModel):
    elevation: float          # z of finished floor
    height: float             # floor-to-floor
    walls: list[Wall]
    rooms: list[Room]         # optional, see §2

class Wall(BaseModel):
    id: str
    start: Vec2; end: Vec2    # centerline
    thickness: float
    height: float | None = None   # defaults to storey height
    openings: list[Opening] = []

class Opening(BaseModel):
    id: str
    kind: Literal["door", "window"]
    along: float              # 0..1 position on the wall centerline
    width: float; height: float
    sill: float = 0.0         # 0 for doors
```

Two things make this pay off later: every entity has a stable `id` (so the agent and the feedback loop can say "widen `window_3`" rather than re-emitting everything), and openings *belong to* walls (parameterized by position along the centerline), so they automatically move when the wall moves. Resist the temptation to store opening positions as world coordinates — that desyncs the moment anything shifts.

## 2. The real fork: wall-centric vs room-centric

This is the design decision that will shape your generator, and it's worth deciding deliberately.

Wall-centric (what your sketch implies) means you place walls and rooms *emerge* as the enclosed faces. It's flexible and freeform, but to know "what rooms exist" — which you need for BOM, for placing doors between adjacent rooms, and for validation — you have to run planar-graph face detection on the wall network, plus solve wall *junctions* (mitering at corners, T-intersections). Junctions are the classic time-sink in procedural architecture; budget for them.

Room-centric means you generate *rooms* first (as rectangles or polygons with target areas), then derive walls on their boundaries, deduplicating shared edges into single walls. Doors go on shared edges between rooms; windows go on exterior edges. This is much easier to keep valid — every room is enclosed by construction — and BOM-per-room is trivial.

For seeded procedural generation, I'd start room-centric, and specifically with a **layout graph → geometry** approach, which is what holds up in the research (it's the tractable version of "make buildings that make sense"):

1. Pick a footprint (union of a few rectangles, parameterized → gives L/T/U shapes).
2. Subdivide it into rooms — binary space partitioning or a squarified treemap targeting per-room areas. Seeded, so reproducible.
3. Emit walls from room boundaries (dedupe shared edges).
4. Place openings: a door on each shared edge to make rooms reachable (you can even verify connectivity as a graph), windows on exterior walls by a spacing rule.
5. Roof from the footprint.

You can still *support* freeform wall-centric specs in the schema; just don't make your generator start there.

## 3. Keep randomness in the generator, determinism in the builder

`generate(seed, params) -> BuildingSpec` is where all the `random` calls live, seeded by `seed`. `build(spec) -> Geometry` must be a pure function — no randomness, no global state. Same spec always yields identical geometry and identical BOM. This separation is what makes the whole thing testable (golden specs, geometry hashes) and what lets the agent reason about edits: it's changing *data*, and the consequences are deterministic.

## 4. The builder, the kernel, and the parts that will bite you

Keep the kernel behind an interface so it's swappable, but for a first backend I'd use **build123d** (OpenCASCADE under the hood): precise dimensions, boolean subtraction for door/window openings, and clean export to STEP *and* mesh formats (glTF/STL) — which matters because you want CAD-accurate quantities but mesh output for rendering. Blender/`bpy` is the alternative if you'd rather have geometry and rendering in one process; the trade-off is messier precision and BOM. Either works behind the interface.

Two things to anticipate:

Wall junctions. Don't try to make the *geometry* perfect for BOM. Build each wall as an extruded box from its centerline, `union` them for the visual solid (the union cleans up corners automatically), but compute the **BOM from the parametric values, not the unioned mesh**. Trying to measure "how much of this wall remains after the corner overlap" from geometry is a rabbit hole; `length × thickness × height` minus opening volumes from the spec is exact and trivial. Decouple "pretty geometry" from "accurate quantities."

Roofs. Flat and shed (mono-pitch) are easy. Gable is a straightforward ridge over a rectangle. For hip roofs over arbitrary footprints, the right general algorithm is the **straight skeleton** — it's the standard way to derive hip-roof ridge lines from a polygon. Start with flat/shed/gable as enum-dispatched generators (`roof_builders[roof.kind]`), add hip via straight skeleton when you need it. Make roof types a registry so adding one is a new function, not a new branch everywhere.

## 5. BOM is a traversal, and it's also free validation

Because the semantic model knows every entity and its dimensions, the BOM is just `sum`/`count` over the spec: wall volume and face area per wall, doors and windows counted by type and size, floor slab area, roof area by pitch. Define a `quantities()` method per entity type and fold them up. Two bonuses: the BOM doubles as a cheap regression check (did this edit unexpectedly triple the glazing area?), and it's the natural seed for an IFC export later, since IFC wants exactly these semantic quantities.

## 6. Spend your feedback budget on validation first, vision second

This is the part people get backwards. Most defects in generated geometry are *detectable without a vision model*, and those checks are essentially free. Run a validator pass over the spec + semantic model and return structured issues as text:

- Geometric: footprint closed and non-self-intersecting; openings fit within their wall's length and height (`along·length ± width/2` in bounds, `sill + height ≤ wall height`); openings on the same wall don't overlap; roof covers the plan.
- Topological: walls form closed loops around each room; every room reachable through doors (connectivity on the room graph); no orphaned walls.
- Architectural sanity: min room area, min ceiling height, door width ≥ threshold.

Feed these back to the agent as a list of violations with the offending `id`s. This catches the overwhelming majority of "broken building" cases deterministically, cheaply, and reproducibly. Reserve the vision model for what validators *can't* judge: "does this look like the prompt's intent — a cozy two-bed cottage?" rather than "is `window_3` inside its wall."

## 7. The visual loop, concretely

When you do render for the vision model, make the renders *legible to a model*, which is different from making them pretty:

- Render a fixed set of **orthographic** views — a top-down plan (the single most informative view for architecture), 2–3 elevations, and one isometric — from a fixed camera per view so frames are comparable across iterations.
- Flat-shade, and color by semantic type (walls one color, doors another, windows another, roof another) so the model can identify elements unambiguously.
- Overlay annotations: dimension lines, room labels, a north arrow, a scale bar, and the entity `id`s. An annotated plan is dramatically more useful to a vision model than a bare render.
- Use a fast offscreen renderer for the loop (export mesh → `pyrender`/`trimesh` headless; the plan can even be a 2D matplotlib/SVG drawing straight from the spec). Save Blender/Cycles for final beauty shots.

The loop itself: build → validators (cheap, text) → if clean, render → vision critique against the prompt → both kinds of feedback come back as **structured spec edits** (e.g. a JSON patch or a list of typed mutations), which you validate before applying → rebuild. Cache renders by `hash(spec) + view`. Cap iterations and track convergence so it can't loop forever.

A subtle but important point: have the agent emit *constrained edits* ("set `window_3.width = 1.2`", "add door between `room_2` and `room_3`") rather than free-form code against your model. The constrained action space is what keeps it out of invalid states — same reason the spec is typed.

## 8. The API surface (design now, wire to agents later)

Sessions hold a spec; everything operates on the session:

```
POST /sessions            {seed, params}     -> {session_id, spec}
GET  /sessions/{id}/spec                     -> spec
POST /sessions/{id}/edit  {mutations: [...]} -> {spec, issues}
GET  /sessions/{id}/validate                 -> {issues: [...]}
GET  /sessions/{id}/bom                      -> {quantities}
GET  /sessions/{id}/render?view=plan|iso|... -> image
POST /sessions/{id}/export {format}          -> file (glTF/STEP/IFC)
```

The granular `edit` mutations *are* the agent's tool definitions later. Keep a free-form "evaluate this Python against the model" escape hatch for power users, but make the typed mutations the default path.

## 9. Cross-cutting, and where I'd start

Fix units and orientation on day one (meters, Z-up, documented origin). Version the schema (`schema_version`) since you'll persist specs and want migrations. Test with golden specs → geometry hashes and golden plan images. For performance, render low-LOD in the loop and cache by spec hash.

For a first milestone I'd deliberately ignore most of this and prove the spine end to end: rectangular footprint only → BSP into rooms → straight walls with box geometry → flat roof → doors on shared edges + windows on exterior walls → glTF export + a plan render + a BOM. No curves, no hip roofs, no materials. Once `generate → build → render → BOM` works for the boring box, every feature you listed (curved walls, roof types, opening placement rules) is an additive change to one layer rather than a rewrite.
