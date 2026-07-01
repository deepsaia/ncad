# ncad — Target Engine Design

**A declarative, parametric *and* direct CAD/CAM/CAE/PCB engine.** Define a part,
an assembly, a mechanism, a machining job, or a board as data — in HOCON
(YAML/JSON load too) — and a pure executor replays that definition against an
exact-geometry kernel to produce solids and surfaces, assemblies, motion,
toolpaths, 2D drawings, PMI, a bill of materials, and renders. Parts may be any
*kind* — solid, surface/freeform, sheet metal, mold/tooling, architecture — each a
**profile** over one common substrate; CAM (a *process* layer over solids) and
PCB/ECAD (a *board data model* that lowers to solids) extend that same substrate.
No GUI for *authoring*; a strong viewer for *seeing*. The same document is
editable by a human, an agent, or a procedural generator, and rebuilds
deterministically. The engine is a backend, intended to be made **public/open**.

**What is proven first vs. designed-for.** The load-bearing spine — CAD (solids,
surfaces, assemblies) plus *kinematics* (the CAE we own) — is what we build and
prove end-to-end early. **CAM** and **PCB/ECAD** are in the mission and in this
design as *first-class seams*: we design their substrate hooks now (so nothing in
the core precludes them) and phase the build late ([`plan.md`](./plan.md)). They
are not "just another geometry profile" — CAM is a *process* profile that consumes
a solid and emits toolpaths; PCB carries its *own* data model (nets, layers,
stackup) and lowers only its board *shape* to the solid substrate. Structural/
thermal/fluid **FEA/CFD stays out of scope** — an export/integration concern, never
a solver we write (§17).

This document is the design for the **target engine**. It describes *what* the
engine is and *why* it is shaped this way. The build-vs-leverage study this
distills lives under [`docs/`](./docs/); the full **feature/operations catalogue
and phased build order** live in [`plan.md`](./plan.md) — this file is
architecture and decisions, not enumeration.

The shift from v1 is one of *generality*, not of philosophy. What genuinely
carries over from the building-only v1 is narrower than "the substrate": the
**spec/IO layer** (HOCON + `jsonschema` + `leaf-common`, returning plain dicts),
the **viewer stack** (glTF tessellation + three.js `nv`), and the *patterns* — the
op-dispatch registry (`roof_builders[kind]` → `feature_ops[op]`), the
traversal-BOM discipline, and determinism-by-construction. What is effectively
**greenfield**: the general geometry kernel interface (v1's `Kernel` is
building-shaped — `box`/`prism`/`arc_wall`), the feature-tree schema, the reference
resolver, and the pure feature executor. The plan is honest about this (§0,
[`plan.md`](./plan.md) "Where we are"): Phase 0 is mostly new code that *reuses v1's
proven patterns*, not an incremental extension of v1's classes.

What is new in capability: motion/kinematics as a first-class output; a *dual*
modeling paradigm (history-based **and** direct/synchronous); parts as multi-domain
**profiles**; drafting, PMI, convergent modeling, and surfacing; CAM and PCB seams;
and a **plugin/converter** ecosystem. The keystone that makes all of it work is the
**reference & naming model** (§2).

---

## 0. Scope and first principles

**General, but proven one slice at a time.** The engine models any solid or
surface part through a feature tree, assembles parts with constraints and joints,
and *drives mechanisms through motion*. We do **not** chase Catia/Creo/NX
feature-parity in one pass (§19, [`plan.md`](./plan.md)); we prove the general
spine on a *boring bracket* and make every later capability an additive change to
one layer rather than a rewrite. This is v1's discipline, generalized.

The domains layer onto that spine in a deliberate order of proof:

- **CAD (proven first)** — solids, surfaces, sheet metal, mold, architecture: the
  feature-tree profiles of §6.
- **CAE = kinematics (proven early, ours)** — DoF/FK/IK/mechanism solve and basic
  MBD (§8). Structural/thermal/fluid analysis is *not* ours (§17).
- **CAM (seamed now, built late)** — a **process profile** (§6a): takes a finished
  solid + stock + fixtures and emits toolpaths → post → G-code. It reuses the solid
  substrate (offsets, sections, booleans, mass props) and adds machining strategy +
  post-processors on top; it authors no new *geometry* profile.
- **PCB/ECAD (seamed now, built late)** — a **board data model** (§6b): nets,
  layers, stackup, footprints, DRC. Only the board *shape* (outline, cutouts,
  copper solids, components) lowers to the solid substrate for MCAD exchange; the
  electrical model is its own sub-document. This is the profile that most stresses
  the substrate's generality, which is exactly why its seams are designed now.

**The one decision that shapes everything (unchanged): separate the *document*
from the *geometry*.** The system is one-way, the document is the single source
of truth, and the executor is a pure function:

```
   authors (human · agent · generator)        document (dict)            model + outputs
                  │                                  │                            │
                  ▼                                  ▼                            ▼
          ┌────────────────┐    document   ┌────────────────────┐ model   ┌──────────────────┐
          │  author / edit │ ────────────► │  executor (pure)   │ ──────► │ validate · BOM · │
          │  the document  │               │  document → model  │         │ motion · draw ·  │
          └────────────────┘               └────────────────────┘         │ PMI · export ·   │
                  ▲                                  ▲                      │ tessellate/view  │
                  │                                  │                      └──────────────────┘
          all authoring &                    no global state;
          randomness here                    deterministic replay
```

- **Document** — structured, validatable data: a feature tree per part, an
  assembly tree, plus optional motion, drawing, and annotation blocks. The single
  source of truth.
- **Executor** — a *pure* function `build(document) → model`. Same document →
  identical geometry, against a pinned kernel (§14).
- **Authors** — anything that *produces or edits* the document: a person, the
  agent layer, or a seeded generator `generate(seed, params) → document`. All
  randomness lives on the authoring side, never in the executor.

**Two modeling paradigms over one model (new, and load-bearing).** The engine
supports both **parametric/history** modeling (the ordered, replayed feature
tree — the default) and **direct/synchronous** modeling (history-free edits that
transform the *current* B-rep in place — move/offset/replace/delete faces, resize
a fillet, make faces coaxial). Both are expressed as operations in the same
document over the same model; §3 details how they coexist, and why direct modeling
is what forces a real persistent-naming layer (§2).

**Parts are profiles over a common substrate (new).** "Solid," "surface,"
"sheet metal," "mold," and "building" are not separate engines — each is a
**profile**: a feature vocabulary plus validators (and, where needed, specialized
representations) layered on the shared kernel, references, executor, sketches,
assembly, and BOM. §6 defines the mechanism. The architecture profile is exactly
this: a *higher-level* profile (storeys/walls/openings) that lowers to substrate
ops — "sheet-metal-like, but more high-level."

**Corollary: keep a *semantic model*, not "just solids."** Features, datums,
parts, ports, joints, drivers, and annotations are first-class. Solids and meshes
are an *output*. This is what makes the result CAD — editable, dimensioned,
motion-capable, exportable to STEP AP242 — rather than extruded blobs.

**The corollary that defines this engine: a reference is not a face number.**
A feature that says "fillet *this* edge," a direct edit that says "offset *that*
face," a joint that pins *this* axis, and a PMI callout on *that* surface all need
to name geometry in a way that survives upstream edits regenerating the topology.
This is the Topological Naming Problem, it is intrinsic and unsolvable-in-full,
and §2 is the engine's answer.

### Cross-cutting conventions (fixed on day one)

- **Units:** the document declares `units` (`"mm"` | `"m"` | `"in"`). The
  **canonical internal unit is millimetres** (build123d default; OCCT is
  unit-agnostic, so a unit is a load-time scale). The building profile sets
  `units = "m"`. **Up axis:** Z-up. **Origin:** documented; world origin at the
  document's reference datum.
- **Angles:** degrees in the document; radians internally.
- **Identity:** every node carries a stable `id` (string), *never reused* even
  after delete — ids anchor references, provenance, joints, and annotations (§2).
- **Versioning:** every document carries a domain `schema_version` (int);
  migrations convert old definitions forward on load (§14, Q6).
- **Determinism:** the executor is pure; `seed` (when a generator is used) is part
  of the document; the kernel version is pinned, because geometry equality — and
  the cache (§4) — is only meaningful against a fixed kernel.
- **Geometry equality (defined, not assumed):** OCCT is **not** bit-reproducible
  across platforms, thread counts, or kernel versions, so equality is *never* a
  raw B-rep byte hash. Two builds are "equal" when their **topology signature**
  (ordered face/edge/vertex counts and surface/curve types) matches **and** their
  **toleranced measures** (volume, total surface area, per-solid bounding box,
  centre of gravity) agree within a documented epsilon. That pair is what golden
  tests compare and what the incremental cache (§4a) trusts as a hit.

---

## 1. The document & spec layer

The document is a plain Python **`dict`**, authored in **HOCON** (JSON and YAML
also load — each is a dict front-end), governed by schemas. We deliberately do
**not** use Pydantic classes in v1: the value of the document is that it is
*validatable*, and the JSON-Schema *vocabulary* (draft 2020-12) + `jsonschema`
delivers that without class boilerplate. As in v1, schemas are authored in HOCON
(inline comments; DRY via `${...}` substitution, not `$ref`), avoiding all
`$`-prefixed keys (HOCON's `$` sigil mangles them); the draft is passed to the
validator explicitly. IO is via `leaf-common` (`EasyHoconPersistence` /
`EasyJsonPersistence`, both returning plain dicts), with `jsonschema` layered on
top — the same path v1 uses.

A document's top-level blocks:

- `parameters` — named values resolved *before* geometry (the expression model,
  below).
- `datums` — named planes, axes, points: the most robust references (§2).
- `parts` — a map of named parts, each an **ordered list of features** (the
  feature tree). A part declares its `profile` (solid | surface | sheet_metal |
  mold | building | …, §6).
- `assembly` — instances of parts plus `constraints`/`joints` (§7).
- `motion` — drivers and motion studies over the assembly's joints (§8).
- `drawings` — derived 2D documentation (§11).
- `annotations` — PMI/GD&T attached to model elements (§11).
- `cam` — machining setups/operations over a built solid (§6a; seamed, phased late).
- `pcb` — the board's electrical data model, lowering its shape to solids (§6b;
  seamed, phased late).

All blocks after `parts` are optional; a single solid part uses only the first
three. `cam` and `pcb` are the *seams* the design commits to now and builds late.

### The expression model — references and functions in HOCON, *logic in code* (Q3)

Parameters are **equations**, not just numbers, but the expression language is
deliberately small. HOCON carries exactly three things:

1. **literals** (`8`, `"mm"`, `[0,0,1]`),
2. **parameter references** and **arithmetic** (`margin = "${hole_d} * 1.5"`),
3. **calls to named functions that are defined in code** —
   `radius = "fillet_for(${thickness}, 'steel')"` — resolved against a
   **registered, sandboxed function library** (pure Python).

What HOCON does **not** carry: control flow, loops, conditionals, or arbitrary
logic-as-text. If logic is needed it lives in (a) a registered function, or
(b) a generator that emits the document. The evaluator is a small safe evaluator
(restricted AST, units-aware) over a function registry; expressions cannot reach
the filesystem, network, or global state.

> **Why.** The document stays declarative, diffable, and safe; the logic stays in
> versioned, unit-tested code — not buried in spec strings. This is the
> FeatureScript-style split (data in the model, behaviour in code) without
> embedding a programming language in the document, and it matches the intent:
> *references and functions in HOCON, logic in code.*

### Shape of a part (abbreviated)

```jsonc
{
  "schema_version": 2, "units": "mm",
  "parameters": { "width": 80, "thickness": 8, "hole_d": 6,
                  "margin": "${hole_d} * 1.5" },        // refs + arithmetic
  "datums":     { "base": { "type": "plane", "ref": "XY" } },
  "parts": {
    "bracket": {
      "profile": "solid",
      "features": [
        { "id": "sk", "op": "sketch", "plane": "datums.base",
          "elements": [ { "id": "r", "type": "rectangle", "w": "${width}", "h": 60 } ],
          "constraints": [ /* planegcs — §5 */ ] },
        { "id": "pad", "op": "extrude", "profile": "sk", "distance": "${thickness}" },
        { "id": "holes", "op": "hole", "on": { "face": "pad.cap(+Z)" },   // generative ref §2
          "diameter": "${hole_d}", "through": true,
          "pattern": { "type": "grid", "nx": 2, "ny": 2, "dx": "${width}-2*${margin}", "dy": 30 } },
        { "id": "soften", "op": "fillet", "radius": 2,
          "edges": "select edges where parallel(Z) and convexity = 'convex'" }  // selector §2
      ]
    }
  }
}
```

---

## 2. The reference & naming model — the keystone

A feature, a direct edit, a joint, and a PMI callout all must *name* the geometry
they touch. When an upstream edit regenerates topology, faces split/merge/renumber
— the **Topological Naming Problem (TNP)**. It is intrinsic to history-based
modeling and *provably impossible to solve perfectly*; the goal is "prefer
references that can't break, and fail loudly at the right node when one does."

A **`Reference`** is a small typed object the resolver turns into concrete
topology at execution time. Four kinds, in robustness order:

| Kind | Example | Resolves via | Survives upstream edits? |
|------|---------|--------------|--------------------------|
| **Semantic** | `datums.base`, `parts.rib`, `holes.instance(0).axis` | name lookup | **Always** — no topology |
| **Generative** | `pad.cap(+Z)` | provenance map (which feature made which element) | **Usually** — re-tagged each rebuild from the op |
| **Selector** | `select edges where convexity='convex'` | predicate over current topology | **Mostly** — breaks only if the edit changes *what matches* |
| **Persistent name** | `#face/pad/27a3` | generative element-mapping layer | **Best-effort** — the fallback; never 100% |

**The provenance map.** The executor maintains, per feature, a map from each
output face/edge/vertex back to the input element(s) and operation that produced
it. It powers generative references, backs the persistent-name fallback, and lets
a validator say *"feature `soften` can no longer find its edges"* with an `id`,
instead of emitting silent garbage.

### Selector grammar — a SQL-style predicate over a versioned attribute model (Q4)

Selectors use a **SQL-`WHERE`-style predicate sublanguage** — honouring the
"zero new system to learn" instinct — but scoped to a *filter predicate*, not full
SQL (no joins, no `FROM` gymnastics):

```
select edges where orientation = 'vertical' and convexity = 'convex' and length > 10
select faces where created_by = 'pad' and type = 'planar' and normal_z > 0
```

The syntax is the *easy* part; the engineering is the **element-attribute
model** — the documented, versioned set of queryable properties: `type`
(planar/cylindrical/conical/spline/…), `created_by` (feature id), `orientation` /
`normal`, `convexity`, `length` / `area` / `radius`, `tangent_to`, adjacency
(`neighbours`), `on_datum`, and so on. That model is what we design carefully and
version; the surface syntax sits on top.

> **Build choice.** Parse the predicate with a small maintained grammar
> (`lark`, on the order of tens of lines) into an AST evaluated against each
> element. If expression needs ever outgrow a `WHERE` clause, adopt **CEL**
> (Google's Common Expression Language; `cel-python`) — a maintained,
> non-Turing-complete spec that hands us the whole evaluator. Selectors version
> *with* the attribute model, so old selectors keep their meaning (§14).

### Persistent names — yes, invest, but phased (Q2)

We **commit to a real generative element-mapping layer** (each output element
gets a stable name derived from its construction history — the approach FreeCAD
1.0 shipped as `TopoShape`). The reason is concrete: **direct/synchronous
modeling (§3), robust dress-up on large parts, joints, and PMI all reference baked
topology**, and selectors alone are too fragile at that scale. It is never 100%,
so it is always paired with loud, id-attributed failure (§10).

The investment is **phased, but de-risked early**: semantic + generative +
selector references carry the spine (Phases 0–2), and — because naming is *the*
keystone and the biggest unknown — a **minimal generative element-map is spiked in
the spine itself** (Phase 0), proven on the boring bracket by surviving a
parameter edit and a feature delete. The *full* TopoShape-style persistent-name
layer then hardens as a defined milestone *before* direct modeling, joints, and PMI
depend on it ([`plan.md`](./plan.md)). Spiking early means the load-bearing risk is
touched on day one, not discovered at Phase 4. This is the generalization of v1's
instinct ("stable `id` + *relative* parameter") into the engine's core: *the
cheapest way to beat TNP is to not create it.*

---

## 3. The two modeling paradigms — parametric and direct

The engine is **dual**, like Creo (Flexible Modeling), NX (Synchronous
Technology), and Catia: a part can be built by replaying history, edited directly
without history, or both.

**Parametric / history (the default).** The ordered feature tree (§4). Edits =
change a feature's parameters or reorder/insert/delete features, then replay.
Fully associative; this is where sketches, equations, and patterns live.

**Direct / synchronous (history-free).** Operations that transform the *current*
B-rep in place by **persistent reference** (§2), without replaying a sketch:
`move_face`, `offset_face`, `replace_face`, `delete_face` / defeature,
`modify_fillet` / `modify_chamfer` (resize baked dress-up), and relational edits
(`make_parallel` / `coaxial` / `tangent` / `symmetric` on dumb geometry). These
are what you use on **imported** geometry (no history to replay) and for quick
late-stage edits.

**How they coexist.** Both are entries in the same document over the same model.
A part is primarily one mode, but — as in Creo — history features may be followed
by direct-edit features appended to the tree (so they remain re-applicable);
imported parts default to direct mode. Direct edits reference geometry by
persistent name rather than by sketch, which is precisely why §2's element-map
layer is a prerequisite for this section.

> **Honesty about the kernel (research-scoped).** OCCT has no turnkey
> synchronous-modeling engine, and its direct-edit pieces have a *narrow* robust
> envelope (investigated, §19):
> - **`delete_face` / defeature** (`BRepAlgoAPI_Defeaturing`) — the most useful
>   native op, but it **fails or hangs on tangent adjacent faces** and can silently
>   corrupt topology. v1 detects tangency and **refuses** rather than risk it.
> - **`offset_face` / thicken** (`BRepOffsetAPI_MakeOffsetShape`) — *whole-shape,
>   Skin-mode only*; fails on C0 splines and past the smallest concave radius. v1
>   restricts to planar/analytic faces within that limit.
> - **`move_face` / `replace_face`** — *no native API*; synthesized from rebuild +
>   boolean + heal, and v1 limits it to **planar faces on well-behaved topology**.
> - Every op is gated by `BRepCheck_Analyzer` **plus an independent
>   volume/area/closedness check** — the analyzer alone can pass invalid results.
>
> So v1 of direct modeling is exactly these **core face ops on well-behaved
> topology**. Full synchronous-tech robustness — auto-inferring and *maintaining*
> relationships as a face moves (Siemens "Live Rules") — is a commercial
> kernel + constraint-solver system (Parasolid + D-Cubed), multi-year and
> PhD-grade; **no OCCT project ships it**. It stays out of v1, `(A)` in
> [`plan.md`](./plan.md), flagged in §19. The remaining unknown is empirical — the
> *success rate* of the well-behaved subset on real imports — which the Phase 4
> spike measures.

---

## 4. The executor and the geometry kernel

`build(document) → model` is a **pure function**. The kernel sits behind a thin
interface so it is swappable and most code never imports it directly.

**v1 kernel: `build123d` (OpenCASCADE / OCP under the hood).** A clean, Pythonic,
Apache-2.0 layer over OCCT (the only mature open B-rep kernel), interchangeable
with CadQuery down to the `.wrapped` shape, with a **raw-OCP escape hatch** for
operations not wrapped first-class (draft, sections, HLR drawings, XCAF
assemblies/PMI). Writing a kernel is a non-goal (§17).

**Op dispatch is a registry.** `feature_ops[feature.op]` dispatches to a per-op
builder — the v1 `roof_builders[roof.kind]` pattern, generalized. Adding an
operation is registering a function. Each op has a **uniform pure signature**:

```
op(shape_in, resolved_params, provenance_in) -> (shape_out, provenance_out, issues)
```

so provenance (§2), per-feature validation (§10), caching, retry, and reordering
all thread through uniformly.

**The rebuild graph.** Features within a part are mostly linear; parameter
expressions, cross-part references, the assembly, and motion create a DAG. The
executor resolves parameters and reference dependencies into a topological order,
then replays. **Content-addressed caching:** each feature's `(inputs + resolved
params)` subtree is hashed; on a CRUD edit only the dirty suffix and its
dependents re-execute. Incremental rebuild is load-bearing — OCP is
single-threaded, and large parts/assemblies (§7) make recompute the dominant cost.

**Failure is a first-class outcome.** OCCT booleans/fillets/lofts/sweeps fail on
real inputs (self-intersection, over-large radii, thin walls, tangency). The
executor validates after *every* feature (§10) and attributes failure to the
offending `id` rather than corrupting downstream geometry; ops stay re-orderable
and the tree inspectable, so a fix is a local edit. The operation→OCCT-family map
and the full feature catalogue live in [`plan.md`](./plan.md).

**Convergent modeling (mesh + B-rep).** Facet (mesh) bodies are first-class
alongside B-rep. The kernel interface admits both, and a pragmatic subset of NX-style
**convergent** operations — boolean between B-rep and mesh, offset/thicken on
facet bodies, and conversion both ways — is built on **Manifold** (`manifold3d`,
Apache-2.0, fast robust mesh booleans, already a dependency) plus OCCT poly.
Full mesh→B-rep reconstruction (reverse engineering) is hard and stays a later/
plugin concern; faceted-as-body and primitive-fit cover the common cases first.

---

## 4a. Determinism, equality & the cache key

The whole design rests on "same document → same model," but OCCT does **not**
guarantee bit-identical B-reps across platforms, thread counts, or kernel versions.
So we define equality and the cache in terms the kernel *can* honour:

- **Equality** (as fixed in §0's conventions) = **topology signature** (ordered
  face/edge/vertex counts + surface/curve types) **plus toleranced measures**
  (volume, surface area, per-solid bbox, CoG) within a documented epsilon. This is
  what golden tests assert and what a cache hit must reproduce. A raw BREP-byte hash
  is deliberately *not* the equality test — it is too brittle to survive an OCCT
  point release.
- **Cache key** (content-addressed, §4) = `hash(resolved feature subtree +
  resolved params + upstream element-map inputs)` **combined with the pinned kernel
  version**. A kernel bump changes every key → cached *geometry* is invalidated
  wholesale (re-execute); document *definitions* are untouched (they migrate via
  §14 converters, not the geometry cache).
- **What the cache stores** — the built shape *and* its provenance/element-map
  slice, so a resumed rebuild restores references, not just geometry.
- **Golden artifacts** — per the testing discipline (`plan.md`): golden *specs*
  (seed+params → document), golden *equality tuples* (topology signature + measures)
  rather than golden BREP bytes, golden *BOM*, and golden *plan/section images* at a
  pinned tessellation deflection.

> **Why this matters now.** Every incremental-rebuild claim (§4), every "identical
> geometry" golden, and the large-assembly out-of-context cache (§7) resolve to
> this definition. Nailing it down here keeps the testing strategy honest rather
> than assuming a reproducibility OCCT does not provide.

---

## 5. Sketches & 2D constraints

A `sketch` feature holds 2D entities (lines, arcs, circles, ellipses, conics,
splines — "Blender-like expressivity, but exact") and constraints (geometric +
dimensional). At resolve time the entity + constraint list goes to a **geometric
constraint solver**, which returns solved positions; the executor builds
wires/faces and feeds them to the sketched features. We **reuse a solver, never
write a GCS** — the candidates and the full sketch-entity/constraint catalogue are
in [`plan.md`](./plan.md); the solver choice is settled in §8/§14 (any license is
acceptable). Conflict/redundancy/DoF status is surfaced as tagged issues (§10);
a fully-constrained sketch is the robust foundation a parametric part wants.

---

## 6. Parts as profiles — solid, surface, sheet metal, mold, building

A **profile** is a part *kind*: a feature vocabulary (a set of `op`s) + validators
+ optional specialized representations, all sharing the substrate (kernel,
references, executor, sketches, assembly, BOM). The substrate knows nothing
domain-specific; each profile registers its ops and rules like a plugin (§14). A
part declares `"profile": "<kind>"`; mixing is allowed where it makes sense (a
solid part with surface features).

- **Solid** *(default)* — the core feature set: sketched features (extrude /
  revolve / sweep / helical sweep / loft), dress-up (fillet / round / chamfer /
  bevel / shell / draft / hole / rib / wrap), patterns/mirror, booleans,
  multibody.
- **Surface / freeform** — surfaces and curves as primary geometry: extruded /
  revolved / swept / lofted surfaces, boundary & fill (n-sided) patches, trim /
  extend / knit / thicken / offset / mid-surface; 3D curves and continuity
  control. **Class A / freeform** (G2–G3 continuity, curvature/reflection
  analysis) is the high end of this profile — genuinely hard, and the most
  aspirational capability in the plan (§19).
- **Sheet metal** — a constrained solid subset (constant thickness, bend
  tables / K-factor): base/edge/miter flange, hem, jog, bend, unfold/fold, and
  **flat-pattern** export, plus reliefs and corner treatments. OCCT has no native
  sheet-metal; it is built from solid ops + bend math + an unfold algorithm
  (FreeCAD's SheetMetal workbench is prior art).
- **Mold / tooling** — parting line & surface, shutoff, core/cavity split,
  shrinkage scale, draft analysis, slider/lifter — built on the surface profile +
  booleans + draft.
- **Building / architecture** — the v1 profile, recast as a **higher-level**
  profile (storeys / walls / openings / roof) that *lowers* to substrate ops
  (sweeps + booleans) while keeping the IFC exchange and the room-graph generator.
  Per the resolution to Q1: *like sheet metal, but more high-level.*

The catalogue of features within each profile is enumerated and phased in
[`plan.md`](./plan.md).

---

## 6a. CAM — machining as a process profile (seamed now, built late)

CAM is **not** a geometry profile; it is a **process** layered over a finished
solid. A CAM *job* is another block in the same document, and it reads the model
the way the BOM does — as a traversal, never a re-measure of a mesh:

```jsonc
"cam": {
  "target": "parts.bracket",              // a built solid (§4)
  "stock":  { "type": "box", "from": "bbox", "offset": 2 },
  "fixtures": [ /* clamps as bodies, for collision */ ],
  "setups": [ { "wcs": "datums.top", "operations": [
    { "id": "face", "op": "face_mill", "tool": "em_10", "stepover": 0.6 },
    { "id": "pocket", "op": "pocket_2d", "on": "select faces where ...", "tool": "em_6" },
    { "id": "drill", "op": "drill", "on": "holes.instances", "cycle": "peck" }
  ] } ]
}
```

- **Substrate reuse.** Toolpath generation leans on operations the solid substrate
  already owns — face/edge **selectors** (§2) to pick machined features, **section**
  and **offset** (§11, §6 surface) for 2.5D/3D contours, **booleans** for stock
  removal simulation, and **mass/volume** deltas (§9) for material-removed BOM.
- **What CAM adds.** Machining **strategies** (facing, 2.5D pocket/contour, drilling
  cycles, later 3-axis surfacing), a **tool library**, feeds/speeds, and
  **post-processors** (strategy-neutral toolpath → machine-specific **G-code**),
  registered like ops. Stock-vs-tool and fixture **collision** reuses the motion
  interference machinery (§8).
- **Scope honesty.** 2.5D milling + drilling + a generic post is the realistic first
  slice; 3+2 and full 3-/5-axis surfacing are long-horizon `(A)`. An external CAM
  kernel (e.g. `opencamlib`-style) is a candidate behind the same op-registry seam,
  or a plugin. The **seam designed now** is: a `cam` block, a toolpath model, and a
  post-processor registry — enough that the substrate provably does not preclude
  CAM, without building it yet.

---

## 6b. PCB / ECAD — a board data model that lowers to solids (seamed now, built late)

A PCB is the one "profile" whose *primary* data is **not** geometry. Its source of
truth is an **electrical** model — a `pcb` sub-document with **nets** (connectivity),
a **layer stackup** (copper/dielectric/mask/silk), **footprints** (component land
patterns), placements, and **routing** (traces/vias/pours). Only the physical
*shape* — board outline, cutouts, copper as thin solids, and component bodies —
**lowers** to the solid substrate, and only when 3D/MCAD output is needed.

- **Two representations, one document.** The electrical model validates and DRCs on
  its own terms (§10 validators generalize: clearance, width, annular ring,
  net-connectivity); the lowered solid representation feeds the viewer (§13),
  STEP/MCAD exchange (§14), and mechanical clearance against an enclosure (§7).
- **Exchange.** ECAD formats — **Gerber / ODB++ / IPC-2581** for fab, and
  **ECAD↔MCAD** (STEP with board+components, or IDF/EMN) for the mechanical side —
  are plugin converters (§14), *not* core. `kicad`-style netlist/footprint import is
  the natural first plugin.
- **Why seam it now, build it late.** PCB stresses the substrate in ways solids
  never do: a non-geometric primary model, layer semantics, and net-level
  validation. Designing the seam now — a `pcb` block that is a peer of `parts`, a
  lowering step to solids, and a DRC validator family — proves the document model
  and reference model (§2) are general enough, and keeps the electrical engine
  itself out of the core until its phase ([`plan.md`](./plan.md)).

---

## 7. Assemblies — instances, constraints, joints, large assemblies

An assembly is **instances of parts** plus relationships. Two complementary
relationship families, both declarative:

- **Assembly constraints** (the mating-condition style): `mate`/`coincident`,
  `align`, `flush`, `offset`, `angle`, `tangent`, `parallel`, `perpendicular`,
  `concentric`, `symmetric`, `distance`, `width`, `lock`.
- **Joints** (the mechanism style, DoF-bearing): `fixed`/`rigid`,
  `revolute`/`pin`, `slider`/`prismatic`, `cylindrical`, `planar`, `ball`/
  `spherical`, `universal`, `screw`, `gear`, `rack-pinion`, `cam`, `belt`,
  `point-on-line`/`slot`.

Both reduce to the same primitive: **named coordinate frames (ports / mate
connectors)** declared on parts, aligned frame-to-frame with offsets and a DoF
signature. This is build123d's Joint model, PartCAD's interfaces/ports, and
Onshape's mate-connectors — the execution target for the declarative blocks. The
joint family is what motion (§8) drives.

We also support **top-down / in-context** design: a **skeleton / master model**
publishes geometry (datums, curves, surfaces) that parts reference, so changing
the skeleton propagates. **Interference / clearance** detection (static here;
motion-time in §8) uses OCCT distance (`BRepExtrema_DistShapeShape`) or fast mesh
intersection (Manifold). BOM and mass properties fold up across instances (§9);
assemblies export through XCAF/XDE so STEP carries structure, colours, names, and
PMI (§11, §14).

### Large assemblies

Real assemblies are too big to re-execute or fully load every time. The design
accommodates scale through:

- **Lightweight representations** — serve tessellation + bounding box + metadata
  for an instance without loading its full B-rep; the document already references
  parts by name, so an instance can resolve to a lightweight rep until detail is
  needed.
- **Lazy / on-demand load** and **display states** — load part definitions and
  geometry only when shown or edited.
- **Simplified representations / LOD** — substitute an envelope box or a decimated
  mesh for distant or out-of-scope parts; a "simplified rep" is a profile-level
  feature.
- **Spatial index** (BVH / octree) — for selection, view culling, and
  interference at assembly scale.
- **Out-of-context build + cache** — parts build independently and cache (§4); the
  assembly composes cached results rather than rebuilding the world.

---

## 8. Motion & kinematics

Motion is a **first-class output**, not a deferred add-on. The assembly's joint
graph (§7) defines degrees of freedom; the motion subsystem drives and solves
them.

- **DoF analysis** — count and identify the mechanism's free degrees of freedom
  from the joint graph (via the constraint solver's Jacobian rank). Report
  over-/under-/exactly-constrained status, like a 3D analogue of sketch DoF.
- **Drivers & forward kinematics (FK)** — assign a **driver** to a joint DoF:
  constant value, linear ramp, a function of time, or a function of another DoF
  (couplers/gears/cams). Sweeping the drivers solves the assembly configuration at
  each step → mechanism motion.
- **Inverse kinematics (IK)** — drive an *output* frame (an end-effector) and
  solve for the joint values that reach it (numerically, by adding the output as a
  constraint).
- **Mechanism solver** — at each time step, fix the driven DoF and solve the
  joint/constraint network for the rest → the assembly's pose. This is the same
  constraint machinery as assembly mating, stepped over time.
- **Interference during motion** — per-step distance/intersection checks between
  moving parts (fast mesh via Manifold, or exact via OCCT), reporting collision
  events and clearances along the motion.
- **Outputs** — **trace curves** (the path of a point), **motion envelopes** (the
  swept volume of a moving body), and **measures over time** (distance, angle,
  velocity, acceleration), all derived and exportable.
- **Multibody dynamics (later)** — force-driven motion: mass/inertia (from
  `BRepGProp`) + gravity, forces/torques, springs/dampers, and contacts → reaction
  forces and accelerations. This is true MBD and the high end of the subsystem;
  **kinematics (geometry-driven) ships first, dynamics (force-driven) later**
  ([`plan.md`](./plan.md)).

**Solver (Q5 — decided: copyleft accepted, the engine is open).** Use
**SolveSpace's solver** (`py-slvs`, GPL-3) for 2D/3D constraint solving and DoF
analysis (sketches, assembly, kinematics), and **OndselSolver** (the multibody
solver from FreeCAD 1.0's Assembly) for mechanism/MBD. `planegcs` remains an
option for 2D. Adopting these GPL components makes the engine itself effectively
**GPL-licensed**, and — given the open/public intent — that is a **settled
decision**, not an open trade-off: an open backend is the goal, and copyleft serves
it. The lone consequence held in view: a *permissive* core (letting third parties
build proprietary tools on ncad) would require permissive solver replacements
(`planegcs` is LGPL; an MBD replacement would need sourcing). The motion model is
solver-agnostic behind a thin interface, so that swap stays possible without
touching the document schema — but it is not a near-term goal (§15, §19).

---

## 9. Bill of materials & mass properties — a traversal, and free validation

The BOM is a **traversal of the model**, never a measurement of the mesh — v1's
principle, generalized from walls/openings to parts / instances / features. Each
op contributes its quantities (a `pattern` knows its count; a `hole` its diameter
and depth); these fold up the part tree, then the assembly tree. **Mass, volume,
centre of gravity, and inertia** come straight from `BRepGProp` / `GProp_GProps`
on the exact solid, feeding both material take-offs and the mass properties motion
dynamics needs (§8). Because the BOM reads the same model the geometry does, a BOM
that cannot be computed is itself a validation signal.

---

## 10. Validators — cheap, deterministic, text-returning

Validators stay as v1 conceived them — **cheap, deterministic, text-returning,
each issue tagged with the offending `id`** — generalized from "broken building"
to "broken feature / topology / constraint." Phases:

- **Pre-build (schema + semantic):** document validates against its schema; refs
  resolve; expressions evaluate; the rebuild graph is acyclic; sketch/assembly DoF
  status is sane.
- **Post-build (geometry):** after each feature, kernel validity checks
  (`is_valid`, BOP checks, `ShapeAnalysis`) confirm a sound result; a failure
  stops the chain and names the node that broke it.

Validators return text, not exceptions, so one surface serves a human at a CLI, an
agent reading a result, and a golden test reading a snapshot.

---

## 11. Drafting, documentation & PMI

**Drafting (2D drawings).** A drawing is a **derived, associative** document:
sheets and title blocks; **views** (base / projected-ortho / isometric /
auxiliary / **section** [full / half / offset / aligned / broken-out] / detail /
broken / crop); **dimensions** (driven, ordinate, baseline, chain);
**annotations** (notes, balloons, centerlines, hatching, weld / surface-finish /
datum / GD&T symbols); and **tables** (BOM, hole, revision). Views are projections
and sections of the model — OCCT's **HLR** (Hidden-Line Removal, `HLRBRep_Algo`)
produces the visible/hidden 2D edges that make an engineering view. Output is
DXF / SVG / PDF; *associative* means the drawing regenerates when the model
changes. The catalogue of view and annotation types is phased in
[`plan.md`](./plan.md).

**PMI / GD&T (3D annotation).** A **semantic annotation model** attached to model
elements (faces, edges, features) via persistent references (§2): datums and datum
targets; geometric tolerances (form / orientation / location / runout);
dimensional tolerances; surface finish; weld symbols; notes — in two forms,
**semantic** (machine-readable, drives downstream manufacturing) and
**presentation** (graphic placement in saved 3D views). PMI is carried through
**STEP AP242** via OCCT's XCAF/XDE (§14). PMI is *the* reason persistent naming
(§2) must be solid: an annotation that loses its face is worse than useless.

---

## 12. The server & API — CRUD over the document

The engine runs as a server holding **sessions**; a session owns a document. The
*only* way to change a document is a **validated dict-patch** against the schema —
so the agent layer (designed-for here, built separately) and a human client share
**one constrained, safe mutation surface**. CRUD maps onto the document tree:

```
POST /docs                            -> { doc_id, document }          # create
GET  /docs/{id}                       -> document                       # read
GET  /docs/{id}/parts/{p}/features    -> [ feature, ... ]               # read tree
POST /docs/{id}/edit  {patches:[]}    -> { document, model, issues }    # C/U/D nodes
GET  /docs/{id}/bom                   -> { quantities, mass_properties }
GET  /docs/{id}/mesh?part=..          -> glTF + element-map
POST /docs/{id}/motion/solve {study}  -> { frames, traces, collisions } # §8
GET  /docs/{id}/drawing/{d}           -> DXF | SVG | PDF                 # §11
POST /docs/{id}/export {format}       -> STEP(AP242) | IGES | glTF | 3MF | DXF
POST /docs/{id}/import {plugin,data}  -> document                        # §14 plugins
POST /docs/{id}/migrate               -> { document, from, to }          # §14 migration
```

Every document carries `schema_version`; an `edit` triggers the incremental
rebuild (§4) and returns model **and** issues together, so *patch → rebuild → see
result + breakage* is a single round-trip. (The natural-language agent
orchestration that drives these endpoints is out of scope here — a wrapper over
the API, not part of the engine.)

---

## 13. Visualization — a viewer, not an editor

The engine ships a strong viewer and **no authoring GUI** (§17). The primary path
reuses v1's stack: the server tessellates OCCT geometry
(`BRepMesh_IncrementalMesh`) to **glTF/GLB**, and the browser renders with
**three.js** (the existing `nv` viewer). An **element-map sidecar** (triangle →
face/edge `id`) turns a passive render into an inspectable model: **picking,
selection, hover-highlight by semantic id, and measurement** — without an editing
UI and without the engine ceasing to be the source of truth. The viewer also
**plays back motion** (§8) by streaming per-frame instance transforms, and
displays PMI/saved views.

**Deferred**, behind the same boundary: OCCT-in-WebAssembly (OpenCascade.js /
`occt-wasm`) for client-side sectioning/measurement; a desktop viewer (Mayo, or
PySide6 over pythonocc's AIS/V3d) if a native app is wanted; and a Blender
beauty-render backend that consumes exported glTF (never the document).

---

## 14. Interchange, plugins & migration

All exchange reads/writes the document or model; none is a second source of truth.

**Core formats.** **STEP** is the backbone — **AP242** for assemblies + PMI via
XCAF/XDE (`STEPCAFControl`), AP203/214 otherwise; plus IGES, **glTF** (viewer/
render), **STL / 3MF / OBJ** (mesh / convergent / print), and **DXF / SVG / PDF**
(2D drawings). FreeCAD is a first-class STEP **round-trip peer**.

**The plugin / converter architecture (Q7).** Importers, exporters, and profiles
are **plugins** registered against a stable contract: *(external format) ⇄ (ncad
document or sub-model)*. **PartCAD compatibility ships as a plugin converter**
(PartCAD YAML ⇄ ncad document) — isolated, maintainable, and *not* a core burden;
other ecosystems (OpenSCAD, vendor formats, future tools) follow the same
contract. The core stays lean; breadth grows at the edges.

```
plugins/
  partcad/      # PartCAD YAML  <-> ncad document   (Q7)
  openscad/     # .scad         -> ncad (import)
  step_ap242/   # STEP+PMI      <-> ncad (core-adjacent)
  <others>/     # same contract: convert to/from the document model
```

**Versioning & migration (Q6).** Every document (part / assembly / motion /
drawing) carries a domain `schema_version`. On load, ncad validates the version;
if it predates the current release, the user is offered an **upgrade** that runs
registered **migration converters** (chained vN→vN+1) — transforming the
*definition* (data), not the geometry, exactly as commercial tools prompt
"convert to current version?" on opening old files. Cache keys include the kernel
version (§4); a kernel bump invalidates cached *geometry* wholesale (re-execute),
while *definitions* migrate via converters. The migration registry is small,
ordered, and tested.

---

## 15. Environment and dependencies

- **Python 3.13**, `.venv` pinned via `uv`, as v1.
- **Geometry:** `build123d` + `cadquery-ocp` (OCCT). **Pin both** — geometry
  equality and cache keys (§4) need a fixed kernel.
- **Solvers:** `py-slvs` (SolveSpace, 2D/3D constraints + DoF) and/or
  `OndselSolver` (multibody/mechanism); `planegcs` optional for 2D. **License is
  copyleft-accepted** (§8, Q5): the engine is public/open, so GPL components are
  used and the engine is therefore **GPL-licensed** (settled, §19). A permissive
  core would need permissive solver replacements — not a near-term goal.
- **Mesh / convergent:** `manifold3d` (Apache-2.0) fast mesh booleans;
  `trimesh` + a glTF writer.
- **Selectors:** `lark` (predicate grammar) — or `cel-python` if escalated (§2).
- **IO / persistence:** `leaf-common` (HOCON/JSON → dicts) + `jsonschema`
  (draft 2020-12), shared with the agent ecosystem.
- **Deferred:** OpenCascade.js (WASM viewer); Blender (render); `ifcopenshell`
  (building profile); **CAM** — `pyclipr` (Clipper2, BSL-1.0) for 2.5D offsets +
  an in-house generic 3-axis post, with `opencamlib` (LGPL-2.1) as the optional 3D
  plugin (§6a); **PCB** — `.kicad_pcb` round-trip + `kicad-cli`/`pcbnew` at arm's
  length, STEP AP214 lowering via build123d (§6b) — all late/plugin. Plugin
  dependencies live with their plugins (§14).

---

## 16. Component boundaries (each unit, one purpose)

| Unit | Purpose | Depends on |
|------|---------|-----------|
| `schema` | feature-tree / assembly / motion / drawing / PMI schemas (HOCON) | — |
| `spec` | load/validate the document (dict) | leaf-common, jsonschema, schema |
| `params` | resolve the expression layer (refs + registered functions, §1) | spec |
| `refs` | reference resolver + provenance map + persistent-name layer (§2) | kernel |
| `kernel` | swappable geometry backend (B-rep + mesh) + build123d impl | build123d, manifold3d |
| `ops` | per-feature builders, by profile (registry, §4/§6) | kernel, refs |
| `sketch` | 2D entities + constraint solving | py-slvs/planegcs, kernel |
| `direct` | history-free face/relational edits (§3) | kernel, refs |
| `build` | pure `build(document) → model`; rebuild graph + cache | spec, params, ops, refs |
| `assembly` | instances, constraints, joints, large-assembly reps (§7) | build, kernel |
| `motion` | DoF, drivers, FK/IK, mechanism/MBD solve, traces (§8) | assembly, py-slvs/Ondsel |
| `validate` | pre-/post-build checks, id-tagged | spec, build |
| `bom` | traversal BOM + mass properties | build |
| `draft` | 2D drawings via HLR; views/dims/annotations/tables (§11) | build |
| `pmi` | semantic GD&T annotation model (§11) | build, refs |
| `export` | STEP AP242 / IGES / glTF / mesh / DXF writers | build, pmi |
| `viewer` | tessellation + element-map + motion playback + three.js | export |
| `cam` *(late)* | machining setups → toolpaths → post-processors → G-code (§6a) | build, ops, motion |
| `ecad` *(late)* | board data model (nets/layers/stackup) + DRC + lowering to solids (§6b) | build, validate |
| `plugins` | importer/exporter/profile converters (PartCAD, Gerber/ODB++, ECAD↔MCAD, …) (§14) | spec, build |
| `migrate` | per-domain schema migration converters (§14) | spec |
| `api` | sessions + dict-patch mutations + endpoints (§12) | build, validate, bom, export, motion |

Dependency arrows point inward toward `build`; nothing downstream reaches back.
`cam` and `ecad` are the two units the design **seams now and builds late** — they
consume `build`'s output and add a process/data layer, never reaching back into it.

---

## 17. Non-goals

Stated explicitly, because scope discipline is what makes the spine provable:

- **No authoring GUI.** The document is authored as text/data; the GUI is a
  *viewer* only (§13).
- **No new geometry kernel.** OCCT via build123d is the floor (§4).
- **No Catia/Creo/NX feature-parity *deadline*.** The full feature set is the
  *plan* ([`plan.md`](./plan.md)), built demand-first over many passes; the
  differentiator is the delivery model (text-defined, version-controlled,
  deterministically rebuilt, motion-capable, BOM-by-construction, agent-editable),
  not a parity date.
- **No simulation solver of our own (FEA/CFD).** Mechanism *kinematics* and basic
  *multibody dynamics* are in scope (§8); structural/thermal/fluid analysis is
  not — it is an export/integration concern. This is the one part of "CAE" we
  deliberately do **not** own.
- **CAM and PCB are in scope as *seams first, build late* — not non-goals.** The
  design commits to their substrate hooks now (§6a, §6b) precisely so they are not
  quietly dropped; what is *not* near-term is the machining-strategy library, the
  post-processor breadth, and the electrical/DRC engine. They are phased at the far
  end of [`plan.md`](./plan.md), not excluded.
- **No full synchronous-technology robustness in v1.** Core direct-edit face ops
  first (§3); auto-maintained relational inference is later/aspirational (§19).
- **Class A surfacing is aspirational, not v1** (§6, §19).
- **No FreeCAD/Blender plugin *core*.** FreeCAD is a parts-bin (solver) and a STEP
  peer; Blender is a render backend.

---

## 18. First milestone & build order

Mirror v1's discipline — make the *boring bracket* work end-to-end before breadth:

> `sketch` (rectangle/circle/polygon) → `extrude`/`pocket` → `hole` → `fillet`,
> built through the `refs` resolver with a live provenance map, exported to glTF,
> shown in the viewer.

**Met when** editing a parameter *or deleting a feature* yields a correct
**incremental** rebuild, and any reference that can no longer resolve is reported
against its `id`. That single loop exercises every load-bearing idea: document as
SOT, pure executor, reference model (§2), cache (§4), id-tagged validation (§10).
Everything after — sketch solver, the full solid feature set, direct modeling,
assemblies, motion, drafting, PMI, surfacing, convergent, the domain profiles, and
the plugin/migration layers — is phased in [`plan.md`](./plan.md).

---

## 19. Open questions

Resolved by this revision (recorded in the decisions log of
[`plan.md`](./plan.md)): **Q1** buildings = a high-level profile that lowers to
substrate ops; **Q2** invest in a generative persistent-name layer, phased, with a
**spike in the spine** (§2); **Q3** HOCON carries refs + registered-function calls,
logic stays in code; **Q4** SQL-`WHERE`-style selector predicates over a versioned
attribute model (`lark`, or CEL if escalated); **Q5** copyleft **accepted** — use
SolveSpace/Ondsel, engine is GPL (settled, no longer open); **Q6** per-domain
`schema_version` + migration converters + an upgrade prompt; **Q7** PartCAD and
friends as plugin converters, not core.

Also resolved this revision: **scope** = CAD + kinematics proven first, **CAM and
PCB seamed now and built late** (§0, §6a, §6b), FEA/CFD out; **determinism** = the
topology-signature + toleranced-measures equality of §4a (not a BREP-byte hash);
**v1-reuse** framed honestly (spec/IO + viewer + patterns carry over; the general
kernel/refs/ops are greenfield).

### Resolved by research (this revision)

Each of these was an open question; a sourced investigation now gives a decision.
The full findings live in [`docs/research/`](./research/); the decisions are here.

- **Direct-modeling ceiling on OCCT — bounded, narrow, and spike-gated.** OCCT
  gives real pieces but a *narrow* robust envelope. `delete_face`/defeature
  (`BRepAlgoAPI_Defeaturing`) is the most useful native op but **fails or hangs on
  tangent adjacent faces** and can silently corrupt topology (tracker-verified);
  `offset_face`/thicken (`BRepOffsetAPI_MakeOffsetShape`) is *whole-shape,
  Skin-mode only*, fails on C0 splines and offsets past the smallest concave
  radius; **there is no native `move_face`/`replace_face`** — it is synthesized
  from rebuild + boolean + heal. **Decision:** v1 direct modeling (§3, Phase 4) is
  scoped to (a) defeature on **non-tangent** faces (detect tangency and *refuse*
  rather than risk corruption), (b) single offset/thicken on planar/analytic faces
  within the concave-radius limit, (c) move/replace on **planar faces of
  well-behaved topology**. Every op is gated by `BRepCheck_Analyzer` **plus an
  independent volume/area/closedness sanity check**, because the analyzer alone can
  pass invalid results (OCCT #1315). **Excluded from v1:** auto-maintained
  relational inference (Siemens Synchronous "Live Rules" is a commercial
  kernel+D-Cubed-solver system, multi-year/PhD-grade — no OCCT project ships it),
  moving faces in fillet/blend/tangent chains, per-face variable offset. Remaining
  unknown → the **spike** (Phase 4, and previewed in bucket 0.5): the empirical
  *success rate* of the well-behaved subset on real dirty imports.
- **Class A surfacing — G2 engineering surfacing is shippable; true Class A is
  out of scope.** OCCT's continuity ceiling is **G2** (`MakeFilling` accepts only
  C0/G1/G2 — *no G3 constraint exists*); curvature *math* is native
  (`GeomLProp_SLProps`), but **zebra/isophote and surface fairing are not** (0 code
  hits; must be built on the curvature primitives). Class A is a *workflow*
  (single-span low-degree patches, interactive control-point sculpting,
  reflection-fairness) that is effectively commercial (Alias/ICEM/CATIA); even
  Rhino is judged below it. **Decision:** ship the **G2 engineering-surfacing
  subset** (Phase 9) — G0/G1/G2 fills and lofts, plus curvature-comb, deviation,
  and a *read-only* zebra/isophote analysis overlay we compute ourselves. True
  Class A (G3, fairing, reflection optimization) is documented **out of scope /
  aspirational `(A)`**, revisited only if a licensable module (e.g. C3D
  FairCurveModeler) can lift G3 without a kernel swap.
- **Kinematics vs MBD depth — rigid-body dynamics yes, deformable/high-fidelity
  contact no.** ncad is a CAD engine, not a physics engine (§17). Kinematics
  (geometry-driven) is core (§8, Phase 6). Force-driven MBD via Ondsel is worth
  exactly what reuses the mass properties we already compute from `BRepGProp`:
  **rigid bodies + gravity + forces/torques + springs/dampers + simple contact**
  (Phase 14). The line is drawn **before** flexible/FEM-coupled bodies and
  friction-rich or continuous contact — those are FEA/physics-engine territory and
  an *export* concern, not ours.
- **Provenance-map cost — budget it O(part topology), lazy for imports.** The
  element-map (§2) is held only for parts **under active edit** and cached beside
  geometry (§4a); **lightweight/simplified reps (§7) carry no map**. For
  direct-mode *imported* bodies (potentially huge face counts, no history) the map
  is **built lazily / on demand** — name an element only when it is referenced.
  Target budget: map memory ≤ a small constant multiple of the body's own B-rep
  topology size; the large-assembly hardening (Phase 12/14) measures and enforces it.
- **Building-profile altitude — stays a thin lowering; no sub-substrate.** The
  point of profiles is *one* substrate. Buildings remain a high-level profile that
  lowers to substrate ops (§6, Phase 11) and keeps IFC + the room-graph generator;
  spaces/systems semantics live **authoring-side** (the generator) and as
  **annotations**, not as a second geometry engine. Revisit only if IFC
  round-trip fidelity provably demands it.
- **CAM kernel — build 2.5D+drilling in-house on Clipper2; opencamlib is the 3D
  plugin; 5-axis is out.** The realistic first slice (§6a, Phase 15) is built on
  **OCCT sections + Clipper2 (`pyclipr`, BSL-1.0)** for the offset/pocket math —
  *not* libarea (unmaintained) and *not* FreeCAD's Path (runtime-coupled). Own the
  strategy logic (contour/pocket/face/drill) and a small generic 3-axis post.
  **`opencamlib` (LGPL-2.1)** sits behind the op-registry seam as an **optional
  plugin** for 3D drop-cutter/waterline finishing. **5-axis has no credible OSS
  kernel → explicitly out of scope**, reserved for a future external-kernel plugin.
- **PCB ownership line — own the data model + geometric DRC + 3D lowering;
  delegate routing/fab to KiCad.** ncad owns (§6b, Phase 16): the **board data
  model** (numbered net table, layer stackup, footprints/pads, tracks/vias/zones,
  drills), **geometric DRC** (clearance, width, annular ring, connectivity — with
  voltage/current/stackup as *inputs*), and **PCB→3D solid lowering** (the
  OCCT/build123d extrude-drill-place-STEP pipeline — squarely our home turf).
  **Delegate** schematic capture, autorouting/placement, physics DRC, and fab
  output (Gerber/drill) to **KiCad** via a **`.kicad_pcb` round-trip**; export
  **STEP AP214** for MCAD (AP242's electrical scope is wire-harness, *not* PCB —
  don't rely on it). Treat zone *fills* as authored input or pin one deterministic
  fill algorithm (the main determinism hazard). First slice proves: text spec →
  board model → geometric DRC → lowered board+component STEP + a `.kicad_pcb`
  round-trip.

### Genuinely still open (empirical / spike-gated)

The decisions above close the *direction*; these remain unknown until measured:

- **Direct-modeling success rate on real geometry.** How often do real dirty
  imports fall inside the narrow robust envelope above? The Phase 4 spike (validity
  pass rate, tangent-failure rate, hang/timeout incidence on representative bodies)
  is designed to close exactly this — the biggest geometry risk.
- **G2 fill/blend robustness on non-trivial surfaces.** OCCT's accumulating
  tolerances and `IsDone()`-failure reports suggest brittleness; only a surfacing
  spike on representative footprints settles how robust the shippable subset is.
- **Provenance-map budget at large-assembly scale.** The O(part-topology) target is
  a hypothesis until Phase 12 measures where it degrades.
- **`.kicad_pcb` *write* round-trip fidelity.** Reading is well-documented; writing
  a KiCad-valid board that survives re-open + DRC + its own STEP export (net
  ordinals, layer tokens, zone fills, 3D-model refs) is the likeliest PCB
  integration risk.
- **MBD contact depth before it stops being CAD.** Rigid + simple contact is in;
  exactly how much contact fidelity is useful before it becomes a physics engine is
  a judgement to revisit against real mechanisms.

*(Settled earlier: the GPL/licensing question — copyleft accepted, §8/§15/§19.)*
