# ncad: Implementation Plan & Tracker

Phased build order with progress tracking for the **target engine**. The design
rationale lives in [`design.md`](./design.md); this file is *what to build, in
what order, and what's done*, and the **feature/operations catalogue** distilled
from Catia / Creo / NX. We will **not** build it all in one pass; phases are
coherent capability slices, each decomposed into **agile buckets**.

**Legend:** `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked ·
`(P)` parallel/cross-cutting · `(A)` aspirational/long-horizon

**Guiding rule, thin vertical slices.** Prove the **general spine end-to-end
first** (Phase 0), then add breadth. Work is organized into **buckets**: each
bucket is a *thin vertical slice* that ends in something you can **author >> build >>
view/export** and *see*, with a concrete **demo** and a **gate**. A bucket is
sized so it can be implemented, tested, and demoed on its own; you never wait for
a whole phase to see a specific capability working. Buckets within a phase are
ordered by dependency; phases and cross-cutting tracks run partly in parallel.

**Near-term optimization:** the fastest path to a *working end-to-end demo*. Phase
0's buckets are ordered so a shape appears in the viewer as early as possible
(0.1), then correctness (incremental rebuild, broken-ref reporting, the TNP spike)
is layered on. Demo-ability leads; breadth follows.

---

## Where we are

**Progress: Phase 0 complete; Phase 1 in progress (buckets 1.1-1.4 done).** The general
spine is proven end-to-end: feature-tree schema, op registry, build123d kernel, the
reference/provenance model (semantic/generative/selector), incremental rebuild with a
content-addressed cache, the §4a equality harness, delete/broken-ref handling + the TNP
spike, and a Three.js viewer (pick-by-id, right data sidebar, orientation gizmo). The
constraint solver (py-slvs/SolveSpace) is integrated with the full entity + constraint +
dimension vocabulary (driven vs driving) and reference-into-sketch (project prior edges,
offset). Sketch status in the viewer (1.5) done, **Phase 1 complete**. Phase 2: STEP
export (2.0), extrude/pocket (2.1), revolve/groove (2.2), sweep (2.3) done. The spline /
curve entity bucket (2.3.5: `bezier` + `interpolated` sketch entities, points solved /
curve derived) is done, so sweep/loft paths and profiles now carry smooth curves. NEXT:
2.4 (loft), which consumes spline profiles/guides. Deferred curve follow-ups: a
solver-capability bucket for true curve constraints (tangent-to-spline, point-on-spline,
G2 smooth); general B-spline / NURBS with weights / endpoint tangents / periodic splines;
and spline edge projection in `_project_edge`.

v1 proved the *pattern*: `spec >> build >> BOM >> view`, determinism, build123d/OCCT,
HOCON+jsonschema, traversal BOM, the Three.js viewer, on the **building profile**
(footprint >> rooms >> walls >> openings >> roof).

**What actually carries into Phase 0 (be honest about it):**

- **Reused directly:** the `spec`/IO layer (HOCON + `jsonschema` + `leaf-common` >>
  plain dicts), the `viewer` stack (glTF tessellation + three.js `nv`), and the
  *patterns*: op-dispatch registry (v1 `roof_builders[kind]` >> `feature_ops[op]`),
  traversal-BOM discipline, id-tagged validators, determinism-by-construction.
- **Effectively greenfield:** v1's `Kernel` is building-shaped (`box`, `prism`,
  `arc_wall`, `sphere`, `barrel`); the *general* kernel interface (sketch / extrude
  / fillet / boolean + a provenance map), the feature-tree schema, the reference
  resolver, and the pure feature executor are **new code**. Phase 0 reuses v1's
  proven *patterns*, not its building-specific classes.

The target engine generalizes the building-specific schema into a **feature tree**
and adds dual modeling, assemblies, motion, drafting, PMI, surfacing, convergent
modeling, the domain profiles, CAM/PCB seams, and a plugin layer.

> The building roadmap (old Phases 6–13: roofs, multi-storey, IFC, agents, render
> tiers) continues as the **building-profile track** (Phase 11) on top of the
> general substrate, not discarded, recast.

---

## Roadmap at a glance

| Phase | Theme | Track | Status |
|-------|-------|-------|--------|
| 0 | The general spine (sketch>>extrude>>hole>>fillet, refs+provenance) | core | `[x]` |
| 1 | 2D sketching & the constraint solver | core | `[~]` |
| 2 | Core solid features (sketched + dress-up) | solid | `[ ]` |
| 3 | Patterns, transforms, booleans, multibody | solid | `[ ]` |
| 4 | Persistent-name layer + direct/synchronous modeling | core | `[ ]` |
| 5 | Assemblies: constraints, joints, in-context | assembly | `[ ]` |
| 6 | Motion & kinematics | motion | `[ ]` |
| 7 | Drafting & documentation (2D drawings) | docs | `[ ]` |
| 8 | PMI / GD&T | docs | `[ ]` |
| 9 | Surfacing & freeform (Class A `(A)`) | surface | `[ ]` |
| 10 | Convergent modeling (mesh + B-rep) | core | `[ ]` |
| 11 | Domain profiles: sheet metal · mold · building | profiles | `[ ]` |
| 12 | Large-assembly performance | assembly | `[ ]` |
| 13 | Interchange & plugins (STEP AP242, mesh, DXF, PartCAD) | interop | `[ ]` |
| 14 | Multibody dynamics · advanced surfacing · hardening | motion/surface | `[ ]` |
| 15 | **CAM seam & first toolpaths** (process profile) `(A)` | cam | `[ ]` |
| 16 | **PCB/ECAD seam & board-to-solid** (data-model profile) `(A)` | ecad | `[ ]` |
| P | References/provenance · caching · viewer · testing · migration | cross-cutting | `[~]` |

> **Buckets, not just phases.** Each phase below is decomposed into numbered
> buckets (e.g. `0.1`, `0.2`), thin vertical slices, each with its own demo +
> gate. The phase gate is met when its buckets are. Only Phase 0 is fully
> bucketed inline here as the exemplar; later phases list buckets as their
> checkboxes and split their gate per slice.

---

## Phase 0: The general spine

**Goal:** one boring bracket, end-to-end, exercising every load-bearing idea.
Reuses v1's *patterns* + spec/IO + viewer; the general kernel/refs/ops/executor are
new code (see "Where we are"). **This is the exemplar of bucketed slicing**: each
bucket below ends in a viewable/inspectable result.

**Bucket 0.1: First shape on screen** *(demo-first)*
- [x] Minimal **feature-tree schema** (`schema/part_schema.hocon`): `parameters`,
      `datums`, `parts[features]`, stable `id`, `schema_version`, `profile`
      (default `solid`), only enough for a sketch + extrude
- [x] **Op registry** (`ops`): `feature_ops[op]` dispatch; uniform pure signature
      `(shape_in, params, prov_in) >> (shape_out, prov_out, issues)`
- [x] Ops `sketch` (rectangle) + `extrude`; general **kernel** interface v0 over
      build123d
- [x] **glTF export**; the `nv` viewer shows the extruded block
- **Demo:** author a rectangle+extrude HOCON >> `ncad build` >> block appears in `nv`.
- **Gate:** a hand-authored document renders in the viewer.

**Bucket 0.2: The everyday ops + expressions**
- [x] Ops `pocket`, `hole`, `fillet`, `chamfer`, `boolean`; sketch `circle`/`polygon`
- [x] **Expression layer** (`params`): `${ref}` + arithmetic + registered-function
      calls; restricted-AST safe evaluator; units-aware (design §1, Q3)
- **Demo:** the bracket (rect >> extrude >> 4 holes via a `margin = ${hole_d}*1.5`
      expression >> edge fillet) builds and renders.
- **Gate:** the boring bracket builds from a parametric document.

**Bucket 0.3: References, provenance & selection**
- [x] **Reference resolver v0** (`refs`): semantic + generative + selector refs
- [x] The **provenance map** (output element >> producing feature/op), threaded
      through every op's signature
- [x] **Element-map sidecar** on glTF; viewer **picks/selects by `id`**
- **Demo:** click a face in `nv` >> it reports the feature `id` that made it;
      `hole on pad.cap(+Z)` resolves via provenance.
- **Gate:** generative + selector references resolve; picking reports semantic ids.

**Bucket 0.4: Incremental rebuild & determinism**
- [x] **Executor** (`build`): rebuild DAG, topological order, per-feature
      validation gate
- [x] **Content-addressed cache** keyed on `hash(subtree+params)` + pinned kernel
      version (design §4a); dirty-suffix re-execution
- [x] **Equality harness** (design §4a): topology signature + toleranced measures,
      the golden comparator (not BREP bytes)
- [x] Golden tests: same document >> equal geometry; **edit-a-param** >>
      correct incremental rebuild
- **Demo:** change `thickness`, only the dirty suffix rebuilds; golden equality holds.
- **Gate:** editing a parameter yields a correct incremental rebuild against the
      §4a equality definition.

**Bucket 0.5: Delete-a-feature, broken refs, and the TNP spike**
- [x] **Delete/insert/reorder** features >> correct incremental rebuild
- [x] **Broken-reference reporting:** an unresolvable ref is attributed to its `id`
      (id-tagged issue), never silent garbage
- [x] **TNP spike** (design §2): a *minimal generative element-map* proven on the
      bracket: a fillet's edge reference survives a parameter edit and an upstream
      feature delete, or fails loudly by `id`. Proves the persistent-name approach
      before Phase 4 hardens it.
- **Demo:** delete the extrude feature >> the dependent fillet reports "cannot find
      its edges" against its `id`; edit an upstream param >> the fillet's edge ref
      still resolves.
- **Gate (Phase 0):** edit a parameter *or delete a feature* >> correct incremental
      rebuild; any unresolvable reference is attributed to its `id`; the element-map
      spike survives an edit (design §18).

---

## Phase 1: 2D sketching & the constraint solver

**Goal:** "Blender-like expressivity, but exact." Reuse a solver (`py-slvs` /
SolveSpace, adopted); never write a GCS. **Depends on** Phase 0. Decomposed into
five buckets; the phase gate is the 1.5 gate.

**Bucket 1.1: Solver seam + first constrained sketch** `[x]`
- [x] **Solver seam:** `SketchSolver` ABC + `SlvsSolver` (py-slvs); solve in 2D,
      expose DoF/conflict/redundancy as id-tagged issues (`BuildIssue` gained a
      `level`: under-constrained is a warning, not a failure)
- [x] Entities `point`, `line`; constraints `coincident`, `horizontal`, `vertical`,
      `distance`; additive `entities`+`constraints` schema alongside primitive `elements`
- **Gate:** a constrained line profile solves and extrudes; over/under-constrained
      reports cleanly. **(done)**

**Bucket 1.2: The full entity vocabulary** `[x]`
- [x] First-class `arc` and `circle` entities + `radius` constraint; `polyline`/`slot`/
      regular-`polygon` sugar lowered by `EntityExpander`; `WireOrderer` orders mixed
      line/arc loops (CCW-reoriented so pockets cut correctly); `kernel.wire_face`
- **Gate:** a profile mixing lines + arcs + a circle solves and builds. **(done)**

**Bucket 1.3: The full constraint vocabulary + dimensions** `[x]`
- [x] **Geometric constraints:** collinear, concentric, parallel, perpendicular,
      tangent, equal, symmetric, midpoint, point-on-entity, fix/ground (dispatch-table
      handlers; ConstraintError surfaces as an id-tagged inconsistent result)
- [x] **Dimensional constraints:** angle, diameter (radius shipped in 1.2); **driven vs
      driving** dimensions (driven = measured post-solve into `SolveResult.measurements`,
      not enforced). Driving arc-length deferred (arc_length is driven-measure only).
- **Gate:** a fully-constrained dimensioned profile drives a feature; driven dims read
      back. **(done)**

**Bucket 1.4: Reference-into-sketch (+ offset)** `[x]`
- [x] **Reference-into-sketch:** a sketch `project` field resolves references to a prior
      feature's edges; `kernel.project_edges` projects them onto the plane; `EdgeProjector`
      makes fixed `construction` reference entities (pinned, excluded from the wire)
- [x] **Offset:** an `offset` entity derives a real entity (line parallel; circle/arc
      radius +/- d); zero-padded generated ids (`PaddedNaming`)
- **Gate:** a sketch that projects a prior face edge and offsets it builds. **(done)**

**Bucket 1.4b: Sketch modify , transforms** `[x]`
- [x] **Transforms:** move, rotate, scale, mirror, sketch pattern (linear/circular) as a
      `TransformApplier` pre-solve stage after `EntityExpander`; copies are fixed
      primitives (positions locked, like `OffsetApplier`); `TransformError` surfaces as an
      id-tagged issue. move/rotate/scale replace in place; mirror/pattern append copies
      (a mirror welds points on the axis so the halves close into one loop).
- **Gate:** a mirrored half-profile builds a closed face; a linear/circular pattern
      replicates entities (multi-loop face deferred). **(done)**

**Bucket 1.4c: Sketch modify , topology** `[x]`
- [x] **trim, extend, corner fillet, corner chamfer** as a `TopologyApplier` pre-solve
      stage (before `TransformApplier`); intersections from seed coords via a shared
      `GeometryIntersector`; results are fixed primitives; `TopologyError` surfaces as an
      id-tagged issue. Corner fillet/chamfer handle line-line corners. Trim/extend weld a
      new endpoint onto a coincident existing point so loops stay closed.
- [x] **Solver hardening:** accept redundant-but-consistent solves (SolveSpace code 5),
      needed because a fixed arc's equal-radius coupling makes its point pins redundant;
      and surface a part's build-failure reasons in the build log (CLI/viewer).
- **Gate:** a sketch trimmed + mirrored builds; a linear sketch pattern replicates. **(done)**

**Bucket 1.4d: Sketch modify , split + whole-loop offset** `[x]`
- [x] **split** (cut an entity in two at a point), **line-arc / arc-arc corner
      fillet/chamfer** (extends 1.4c line-line), and **whole-loop `loop_offset`** (mitre +
      round corners) as `TopologyApplier` ops built on a shared `EntityOffsetter`;
      `loop_offset` replaces the source loop (single-loop; negative distance insets
      regardless of winding). Solver rejects a fixed point that drifts off its seed
      (closes the redundant-solve gap from 1.4c).
- **Gate:** a rectangular loop offset inward with mitred corners builds a smaller face. **(done)**

> Remaining sketch-modify long-tail (reflex/self-intersecting offset corners, per-face
> variable offset, conic/G2 rounds) stays deferred to the Phase-2 dress-up buckets;
> sketch-modify (1.4b/c/d) is complete.

**Bucket 1.5: Sketch status in the viewer (Phase 1 gate)** `[x]`
- [x] Sketch constraint status (well/under/over/inconsistent + dof + failing-constraint
      ids) threaded out of the build as `SketchStatus` on `OpResult`, written to a
      `<stem>.status.json` sidecar, logged per-sketch on the CLI, and shown as a
      collapsible status badge in the viewer sidebar.
- **Gate (Phase 1):** an over/under-constrained sketch solves or reports cleanly; a
      fully-constrained profile drives a downstream feature. **(done , Phase 1 gate met)**

> **Deferred within Phase 1** (land in the buckets above or a later 1.x): **ellipse +
> elliptical arc**, **conic** (parabola/hyperbola), **spline** (interpolated /
> control-point / B-spline / fit) and the **smooth (G2)** spline constraint, and **text**
> are a later entity bucket (1.6); an **`arc_polar` authoring sugar**
> (`center`/`radius`/`start`/`angle`, lowered by `EntityExpander` into a three-point arc
> plus the equivalent radius + angle constraints, keeping radius/angle in the constraint
> layer rather than duplicating them as entity fields) also lands in 1.6; **intersection
> curves** and **vertex projection** land with 1.4b or later; **multi-loop sketches /
> holes-in-one-sketch** stay deferred (holes come from pocket/hole ops).
> (Construction/reference geometry shipped in 1.4.)

---

## Phase 2: Core solid features (sketched + dress-up)

**Goal:** the everyday mechanical-part vocabulary. **Depends on** Phase 1.

**Buckets (by kernel mechanism):**
- **2.0 STEP export** `[x]` , document-level STEP output + `--format` CLI flag + round-trip
  gate. glb (mesh, viewer) vs STEP (exact B-rep, CAD interchange, design §14).
- **2.1** `[x]` extrude/pocket end-conditions (blind/symmetric/two-side/through-all/
  to-next/to-face/to-surface) + draft + thin. Widened `Kernel.extrude` contract; shared
  `extrude_params` vocabulary; `to`-face ref via the ref model.
- **2.2** `[x]` revolve / groove (angle / symmetric / thin; axis X/Y/Z or {point,dir};
  axis-by-reference deferred with datums). Pappus-volume FakeKernel model.
- **2.3** `[x]` sweep (single-path / helical / guide-curve / variable-section). Sketch
  `open` mode yields a wire path; helix generated. Paths: line + arc + helix (smooth
  spline paths follow with the spline entity bucket, sweep picks them up for free).
- **2.4** loft / blend (multi-section, tangency/curvature).
- **2.5** rib / web / stiffener.
- **2.6** fillet/chamfer variants (variable-radius/face/full-round; distance-angle/
  two-distance/vertex).
- **2.7** shell + draft (dress-up ops).
- **2.8** hole wizard (counterbore/countersink/tapped/thread) + wrap.
- **2.9** Phase 2 gate part (bracket + holes + revolved boss + swept rib + variable
  fillet) builds deterministically and exports clean STEP.

**Sketched (additive/subtractive) features**
- [ ] **Extrude / Pad**: blind, symmetric, two-side, through-all, to-next,
      to-face, to-surface; with **draft**; **thin** (wall) option
- [ ] **Pocket / Cut**: same end-condition + draft + thin options
- [ ] **Revolve / Groove**: angle, to-reference, symmetric, thin
- [ ] **Sweep**: single path; with **guide curves**; variable-section sweep;
      normal-to-path / keep-orientation; (OCCT `BRepOffsetAPI_MakePipeShell`)
- [ ] **Helical sweep / coil**: constant & variable pitch
- [ ] **Loft / Blend**: multi-section; guide curves; centerline; ruled; closed;
      start/end **tangency & curvature** conditions (OCCT `ThruSections`)
- [ ] **Rib / web / stiffener**

**Dress-up (applied) features**
- [ ] **Fillet / Round**: constant; **variable-radius**; multi-edge; **face
      fillet**; full-round; setback; conic/G2 rounds; by-rule
- [ ] **Chamfer / Bevel**: distance; distance-angle; two-distance; vertex
- [ ] **Shell / Hollow**: uniform, multi-thickness, faces-to-remove
- [ ] **Draft**: neutral plane; parting-line; step; variable (OCCT
      `BRepOffsetAPI_DraftAngle`, raw OCP)
- [ ] **Hole**: simple / counterbore / countersink / clearance / **tapped**;
      standards-aware (ISO/ANSI) "hole wizard"; **thread** (cosmetic vs modeled)
- [ ] **Wrap**: emboss/engrave sketch or text onto a face
- [ ] Thickness / offset; replace-face / delete-face (preview of Phase 4 direct ops)

**Gate:** a non-trivial part (bracket + holes + revolved boss + swept rib +
variable fillet) builds deterministically and exports clean STEP.

---

## Phase 3: Patterns, transforms, booleans, multibody

**Goal:** replication and body algebra. **Depends on** Phase 2.

- [ ] **Patterns:** linear, circular/polar, **curve-driven**, sketch-driven,
      table-driven, fill, geometry-pattern, pattern-of-pattern (build123d
      `GridLocations`/`PolarLocations` + fuse)
- [ ] **Mirror:** feature, body, face
- [ ] **Transforms:** move/copy body, rotate, scale (uniform & non-uniform via
      `gp_GTrsf`)
- [ ] **Booleans:** union/add, subtract/cut, intersect/common, split body,
      combine; **multibody** management (merge scope, local operations)
- [ ] Body list / show-hide / per-body material (feeds BOM & mass props)

**Gate:** a multibody part with a circular pattern of cut features and a
mirror rebuilds correctly and reports per-body mass properties.

---

## Phase 4: Persistent-name layer + direct/synchronous modeling

**Goal:** the generative element-map (design §2, Q2) and history-free editing
(design §3). **Prerequisite for** robust PMI (8), joints (5), surfacing (9).

> **Research-scoped envelope** (design §3, §19; `docs/research/direct-modeling-occt-ceiling.md`).
> OCCT's direct-edit robustness is narrow. v1 targets **well-behaved topology only**
> and refuses rather than risks corruption; every op is gated by
> `BRepCheck_Analyzer` **plus** an independent volume/area/closedness check.

**Bucket 4.0: De-risking spike (do first)**
- [ ] On a representative dirty STEP import, run **defeature + planar move_face +
      heal**; measure validity-gate pass rate, tangent-face failure rate,
      hang/timeout incidence. This sets the achievable envelope before building on it.
- **Gate:** a measured success-rate report exists; the envelope is written down.

**Bucket 4.1: Persistent-name layer**
- [ ] **Persistent-name layer:** stable element names from construction history
      (TopoShape-style); round-trip through edits; expose as `#face/...` refs
      (hardens the bucket-0.5 spike)

**Bucket 4.2: Direct face ops (well-behaved only)**
- [ ] `delete_face`/**defeature** (`BRepAlgoAPI_Defeaturing`): **non-tangent**
      adjacent faces only; detect tangency and **refuse**
- [ ] `offset_face`/thicken: planar/analytic faces, single offset < smallest local
      concave radius; reject C0 BSpline surfaces
- [ ] `move_face`/`replace_face`: planar faces on well-behaved topology
      (rebuild + boolean + `UnifySameDomain` + `ShapeFix`)
- [ ] **Direct dress-up edits:** resize baked `fillet`/`chamfer`; reposition baked `hole`

**Bucket 4.3: Imported & mixed mode**
- [ ] **Imported-geometry mode:** STEP/IGES import >> editable direct body
- [ ] **Relational direct edits:** parallel / coaxial / perpendicular / tangent /
      symmetric / coplanar (on history-free geometry)
- [ ] Mixed mode: direct-edit features appended after a history tree (Creo-style)

**Gate (Phase 4):** import a dumb STEP solid, defeature + move a planar face + resize
a fillet directly within the measured envelope, and re-export, references survive;
out-of-envelope inputs are **refused with an id-tagged reason**, never silently
corrupted.

> **Excluded from v1** (`(A)`, design §19): auto-*maintained* relational inference
> ("Live Rules" = commercial kernel + D-Cubed solver, multi-year), moving faces in
> fillet/blend/tangent chains, per-face variable offset, self-intersecting offsets.

---

## Phase 5: Assemblies: constraints, joints, in-context

**Goal:** instances + relationships; the joint graph motion (Phase 6) drives.
**Depends on** Phase 4 (persistent refs to mating faces/axes).

- [ ] **Instances & structure:** components, sub-assemblies, flexible
      sub-assemblies, replace/pattern/mirror component
- [ ] **Mate connectors / ports:** named coordinate frames on parts (the shared
      primitive for both families below)
- [ ] **Assembly constraints:** mate/coincident, **align**, **flush**, **offset**,
      angle, **tangent**, parallel, perpendicular, concentric, symmetric, distance,
      width, lock
- [ ] **Joints (DoF-bearing):** **fixed/rigid**, **revolute/pin**,
      **slider/prismatic**, cylindrical, planar, **ball/spherical**, universal,
      screw, gear, rack-pinion, cam, belt, point-on-line/slot
- [ ] **Top-down / in-context:** skeleton / master model; publish geometry; change
      propagation
- [ ] **Interference / clearance** (static): exact (`BRepExtrema_DistShapeShape`)
      or fast mesh (Manifold)
- [ ] **Assembly BOM** across instances + roll-up mass properties; balloons later
      (Phase 7)
- [ ] **Exploded views** (definition; rendered in viewer)

**Gate:** a two-part mated assembly with one revolute joint exports as structured
STEP (AP242) and opens in FreeCAD; interference check is correct.

---

## Phase 6: Motion & kinematics

**Goal:** drive and solve the mechanism (design §8). **Depends on** Phase 5.

- [ ] **DoF analysis:** free degrees of freedom from the joint graph; over/under/
      exactly-constrained status (solver Jacobian rank)
- [ ] **Drivers / forward kinematics:** per-joint driver: constant, linear ramp,
      function-of-time, function-of-another-DoF (couplers/gears/cams); sweep >>
      configuration per step
- [ ] **Inverse kinematics:** drive an output frame, solve joint values
- [ ] **Mechanism solver:** step time, fix driven DoF, solve constraint network
      (`py-slvs` / Ondsel)
- [ ] **Interference during motion:** per-step collision/clearance; collision
      events on the timeline
- [ ] **Outputs:** **trace curves** (point path), **motion envelopes** (swept
      volume), **measures over time** (distance/angle/velocity/accel)
- [ ] **Viewer playback:** stream per-frame instance transforms; scrub timeline
- [ ] Motion study definitions persisted in the `motion` block

**Gate:** a four-bar linkage animates from a single angular driver; a trace curve
and a collision-free report are produced and exported.

---

## Phase 7: Drafting & documentation (2D drawings)

**Goal:** associative engineering drawings (design §11). **Depends on** Phase 2;
**uses** OCCT **HLR** (`HLRBRep_Algo`).

- [ ] **Sheets & formats:** sizes, title blocks, borders, zones
- [ ] **Views:** base/front, projected ortho, isometric, **auxiliary**,
      **section** (full / half / **offset** / **aligned** / broken-out),
      **detail**, broken, crop
- [ ] **Dimensions:** driven (model-linked), ordinate, baseline, chain;
      tolerance display
- [ ] **Annotations:** notes, **balloons**, centerlines/center-marks, hatching,
      leader lines
- [ ] **Symbols:** surface-finish, weld, datum, GD&T frames (presentation; PMI
      source in Phase 8)
- [ ] **Tables:** **BOM table**, hole table, revision table
- [ ] **Associativity:** drawing regenerates on model change; output DXF / SVG / PDF

**Gate:** a part drawing with a section view, auto-BOM table, and balloons
regenerates after a model edit and exports to PDF/DXF.

---

## Phase 8: PMI / GD&T

**Goal:** semantic 3D annotation (design §11). **Depends on** Phase 4 (persistent
refs); **carried by** STEP AP242 (Phase 13).

- [ ] **Annotation model:** attach to faces/edges/features by persistent name
- [ ] **Datums & datum targets**
- [ ] **Geometric tolerances:** form (flatness/straightness/circularity/
      cylindricity), orientation (parallelism/perpendicularity/angularity),
      location (position/concentricity/symmetry), runout
- [ ] **Dimensional tolerances**, **surface finish**, **weld symbols**, notes
- [ ] **Two forms:** semantic (machine-readable) + presentation (graphic in saved
      views)
- [ ] **Saved 3D views**; PMI shown in the viewer
- [ ] Validation: every annotation resolves to a live element (else id-tagged
      failure)

**Gate:** a part with datums + a position tolerance + surface finish round-trips
through STEP AP242 with PMI intact.

---

## Phase 9: Surfacing & freeform

**Goal:** surfaces and curves as primary geometry; the hard geometry domain
(design §6). **Depends on** Phase 1–2.

**Curves**
- [ ] 3D spline (interpolated / control-point / fit), helix, projected curve,
      intersection curve, curve-on-surface, isocline, bridge/blend curve,
      composite/combine curve, curve from equation

**Surfaces**
- [ ] Extruded / revolved / swept / lofted surface
- [ ] **Boundary blend** (surface from boundary curves, Creo/Catia)
- [ ] **Fill** (n-sided patch), ruled surface, offset surface, **mid-surface**
- [ ] Trim / untrim, extend, **knit/sew**, thicken
- [ ] Sweep / loft with **tangency & curvature** conditions

**G2 engineering surfacing + analysis (shippable; design §6, §19;
`docs/research/class-a-surfacing-feasibility.md`)**
- [ ] Edge **match / blend** to **G0 / G1 / G2**: G2 is OCCT's ceiling
      (`MakeFilling` accepts only C0/G1/G2; **no G3**); validator asserts achieved
      continuity via `BRepLProp::Continuity` at seams
- [ ] **Analysis (we build on `GeomLProp_SLProps` + `BRepExtrema_DistShapeShape`):**
      curvature comb, Gaussian/mean curvature, deviation/gap report,
      **zebra / isophote overlay** (read-only quality check, not a fairing optimizer)

**Class A / true freeform `(A)`: out of scope on OCCT, revisit only via specialist**
- [ ] G3 continuity, control-point sculpting, curvature *fairing*, reflection-fairness,
      a *workflow* (Alias/ICEM/CATIA), effectively commercial; OCCT cannot reach it.
      Revisit only if a licensable module (e.g. C3D FairCurveModeler) lifts G3 without
      a kernel swap (design §19).

**Gate (v1 of phase):** a lofted surface with **G2** boundary conditions, thickened
to a solid, with a curvature-comb + zebra analysis view and a seam-continuity
assertion. (Documented non-goals: no G3, no control-point sculpting, no fairing.)

---

## Phase 10: Convergent modeling (mesh + B-rep)

**Goal:** mesh and B-rep in one model (design §4). **Depends on** Phase 3;
**uses** Manifold (`manifold3d`).

- [ ] **Facet bodies** as first-class (import STL / 3MF / OBJ)
- [ ] **Boolean** B-rep ⊕ mesh
- [ ] **Mesh features:** offset, thicken, fillet-on-facet (pragmatic)
- [ ] **Conversion:** B-rep >> mesh (tessellate); mesh >> B-rep (faceted-as-body +
      primitive fit; full reverse-engineering is `(A)` / plugin)
- [ ] Remesh / decimate / smooth; mesh repair

**Gate:** a B-rep bracket booleaned with an imported scanned mesh exports as a
single watertight body.

---

## Phase 11: Domain profiles: sheet metal · mold · building

**Goal:** specialized part kinds as profiles over the substrate (design §6).
**Depends on** Phase 2 (sheet metal, building), Phase 9 (mold).

**Sheet metal**
- [ ] Base flange/tab, **edge flange**, miter flange, **hem**, **jog**, bend,
      sketched bend, lofted bend, gusset
- [ ] **Unfold / fold**, **flat-pattern** export (DXF), normal cut
- [ ] **Relief:** bend relief, corner relief, closed corner; corner treatments
- [ ] **K-factor / bend tables / bend allowance**; forming tools; cross-break;
      tab/slot

**Mold / tooling**
- [ ] Shrinkage scale, draft analysis
- [ ] **Parting line**, **parting surface**, shutoff surfaces
- [ ] **Core / cavity split**; slider/lifter; runner/gate/ejector layout (basic)

**Building / architecture** *(the v1 profile, recast; Q1)*
- [ ] High-level schema (storeys/walls/openings/roof) **lowering** to substrate
      ops (sweep + boolean)
- [ ] Keep the **room-graph generator** and **IFC** exchange (`ifcopenshell`)
- [ ] Migrate v1 building examples onto the lowered representation
- [ ] (building-profile track: roofs, multi-storey, L/T/U footprints, curved
      corners, carried from the old roadmap)

**Gate:** a sheet-metal part flattens to a correct flat pattern; a simple two-plate
mold splits core/cavity; a v1 building re-builds via the lowered profile.

---

## Phase 12: Large-assembly performance

**Goal:** scale to real assemblies (design §7). **Depends on** Phase 5;
**cross-cuts** caching.

- [ ] **Lightweight representations** (tessellation + bbox + metadata, no full
      B-rep load)
- [ ] **Lazy / on-demand** part load; **display states**
- [ ] **Simplified reps / LOD**: envelope-box or decimated-mesh substitution
- [ ] **Spatial index** (BVH/octree) for selection, culling, interference
- [ ] **Out-of-context build + cache**: compose cached parts, don't rebuild the
      world
- [ ] Sectioning across large assemblies

**Gate:** an assembly of hundreds of instances opens and navigates responsively
with lightweight reps; interference query stays interactive.

---

## Phase 13: Interchange & plugins

**Goal:** exchange + the plugin/converter ecosystem (design §14, Q7).
**Cross-cuts** most phases (exporters land as their features mature).

- [ ] **STEP** AP203/214; **AP242** with **PMI + assembly** via XCAF/XDE
      (`STEPCAFControl`); FreeCAD round-trip
- [ ] **IGES**; **glTF** (viewer/render); **STL / 3MF / OBJ** (mesh); **DXF / SVG /
      PDF** (drawings, flat patterns)
- [ ] **Plugin contract:** *(external format) ⇄ (ncad document / sub-model)*;
      registry under `plugins/`
- [ ] **PartCAD plugin**: PartCAD YAML ⇄ ncad document (target compatibility,
      isolated, maintainable)
- [ ] **Other plugins** (same contract): OpenSCAD import; vendor/format converters
- [ ] (later) JT / 3D-PDF lightweight exchange

**Gate:** a PartCAD assembly imports as an ncad document and re-exports as STEP
AP242 without loss of structure.

---

## Phase 14: Multibody dynamics · advanced surfacing · hardening

**Goal:** the high-end + production polish `(A)`. **Depends on** Phase 6, 9, 12.

- [ ] **Multibody dynamics (MBD), rigid bodies only:** mass/inertia (from
      `BRepGProp`) + gravity, forces/torques, springs/dampers, **simple contact** >>
      reaction forces & accelerations (Ondsel MbD solver). **Line drawn here**
      (design §19): *no* flexible/FEM-coupled bodies, friction-rich or continuous
      contact. That is physics-engine / FEA territory and an export concern (§17).
- [ ] **Advanced surfacing:** true Class A stays **out of scope** unless a licensable
      specialist module (e.g. C3D FairCurveModeler) is adopted (design §19); this
      bucket is that evaluation, not a build commitment.
- [ ] **Robust synchronous tech:** auto-maintained relations on complex topology,
      remains `(A)` (commercial kernel + constraint-solver class of system, design §19)
- [ ] **Performance hardening:** cache tuning, parallelism around OCP's
      single-thread limit, **provenance-map memory budget**: enforce the
      O(part-topology) target, lazy maps for imports (design §19)
- [ ] **Optional WASM client** (OpenCascade.js) for client-side sectioning/measure
- [ ] **Optional desktop viewer** (Mayo / pythonocc); **Blender** beauty render

**Gate:** a pendulum swings under gravity with correct period; the engine handles a
representative large assembly within a defined performance budget.

---

## Phase 15: CAM: the process profile `(A)`

**Goal:** prove the CAM **seam** (design §6a) with a first real toolpath, a
process layer over a built solid, not a new geometry profile. **Depends on**
Phase 2 (solids), Phase 3 (booleans, for stock simulation), Phase 6 (interference,
for collision). Built late; the seam is designed from Phase 0.

**Bucket 15.1: Seam & stock**
- [ ] `cam` document block: `target` solid, `stock` (from bbox / body), `fixtures`,
      `setups[operations]`; validates against schema; no toolpaths yet
- [ ] **Tool library** (diameter/flutes/type) as a registered resource
- **Demo:** a `cam` block loads, resolves its target solid, and shows stock+part in
      the viewer. **Gate:** the block round-trips through spec + validation.

**Bucket 15.2: First toolpaths (2.5D + drilling)**
- [ ] Strategies `face_mill`, `pocket_2d` (selector-driven), `contour`, `drill`
      (G81/G83 cycles); toolpath model (moves, feeds/speeds) built on **OCCT
      sections + Clipper2 (`pyclipr`, BSL-1.0)** offsets: own the strategy logic
      (contour = single tool-radius offset; pocket = concentric inward offsets)
- [ ] Material-removed **BOM/mass delta** (§9) via boolean stock simulation
- [ ] **Collision** (tool/holder/fixture vs stock) reusing motion interference (§8)
- **Demo:** a facing + pocket + drill job on the bracket previews toolpaths in `nv`.
- **Gate:** toolpaths generate for a 2.5D part and show a correct stock-removal preview.

**Bucket 15.3: Post-processor >> G-code**
- [ ] **Post-processor registry** (strategy-neutral toolpath >> machine G-code);
      one **in-house generic 3-axis post** (RS274/NGC vocabulary), pluggable dialects
- **Demo:** the pocket job exports runnable G-code for a generic 3-axis post.
- **Gate:** G-code exports and back-plots to the intended toolpath.

> **Boundary (design §19; `docs/research/cam-toolpath-kernel.md`):** 3D
> drop-cutter/waterline finishing = **`opencamlib` (LGPL-2.1) as an optional plugin**
> behind the op-registry seam. **5-axis has no credible OSS kernel >> out of scope**,
> reserved for a future external-kernel plugin. Do **not** depend on FreeCAD Path
> (runtime-coupled) or libarea (unmaintained).

---

## Phase 16: PCB / ECAD: the board data-model profile `(A)`

**Goal:** prove the PCB **seam** (design §6b), a board whose *primary* model is
electrical, whose *shape* lowers to solids. **Depends on** Phase 2 (solids for
lowering), Phase 13 (interchange). Built late; the seam is designed from Phase 0.

**Bucket 16.1: Board data model & geometric DRC**
- [ ] `pcb` block (peer of `parts`): **numbered net table**, **layer stackup**,
      **footprints/pads**, placements, tracks/vias/zones, drills; validates against
      schema. Treat zone *fills* as authored input or pin one deterministic fill
      (the main determinism hazard).
- [ ] **Geometric DRC** validator family (§10): clearance, trace width, annular
      ring, net-connectivity, id-tagged issues; voltage/current/stackup as *inputs*
- **Demo:** a small board loads and DRCs; violations report by element `id`.
- **Gate:** a board with a rule violation reports it cleanly.

**Bucket 16.2: Lower to solids + MCAD exchange**
- [ ] **Lowering step** (OCCT/build123d): board outline + cutouts + copper (thin
      solids) + component bodies (placed via XCAF sub-assembly) >> the solid substrate
- [ ] **Board-to-STEP AP214** (with components) for the mechanical side (AP242's
      electrical scope is wire-harness, *not* PCB); enclosure clearance via assembly
      interference (§7)
- **Demo:** the board renders as a 3D solid and exports STEP into an enclosure
      assembly; clearance is checked.
- **Gate:** a board lowers to a correct 3D solid and exports STEP AP214 for MCAD use.

**Bucket 16.3: KiCad round-trip (the delegation seam)**
- [ ] **`.kicad_pcb` read + write** so KiCad owns schematic/routing/placement/fab
      output (Gerber/drill) and physics DRC; `pcbnew` read-only ingest, `kicad-cli`
      at arm's length
- **Demo:** a board round-trips ncad ⇄ `.kicad_pcb`, survives KiCad re-open + DRC.
- **Gate:** the written board is KiCad-valid and re-openable without loss.

> **Ownership line (design §19; `docs/research/pcb-ecad-ownership.md`):** ncad owns
> the data model + geometric DRC + 3D lowering; **delegates** routing, autoplacement,
> fab output, and physics DRC to **KiCad**. Gerber/ODB++/IPC-2581 are **plugin
> converters** (design §14).

---

## Cross-cutting tracks `(P)`

Run alongside the phases, not after them:

- [~] **References & provenance maturity**: selector + generative element-map
      **spike** shipped (buckets 0.3/0.5); the robust persistent-name layer (Phase 4)
      is still ahead. The single most important track.
- [~] **Performance & caching**: content-addressed cache keyed on subtree + pinned
      kernel shipped (bucket 0.4, design §4a); incremental rebuild live. Large-assembly
      budget (Phase 12) ahead.
- [~] **Viewer capabilities**: pick/select shipped (0.3), plus the right data sidebar
      (Hierarchy/BOM/Plan), orientation gizmo, free-look. Next: measure >> motion
      playback (6) >> PMI/saved views (8) >> sectioning (12) >> CAM preview (15).
- [~] **Testing & golden**: the §4a **equality harness** (topology signature +
      toleranced measures, *not* BREP bytes) shipped (bucket 0.4); golden equality
      tuples + fast/slow gate examples per bucket. Ahead: per-feature failure goldens,
      STEP round-trip goldens.
- [ ] **Versioning & migration**: `schema_version` per domain + migration
      converters + "upgrade this design?" prompt (design §14, Q6); keep the
      registry small and tested
- [~] **Docs**: keep `design.md` (architecture) and this file (catalogue) in sync;
      author-facing HOCON reference per profile

---

## Decisions log

**Resolved this revision** (rationale in [`design.md`](./design.md)):

- **A: Motion/kinematics is first-class** (not deferred): joints >> DoF >> drivers/
      FK/IK >> mechanism solve >> traces/envelopes; MBD dynamics later (§8, Phase 6/14).
- **B: Dual modeling paradigm:** parametric/history **and** direct/synchronous
      over one model (§3, Phase 4).
- **B: Parts are profiles:** solid / surface / sheet-metal / mold / building share
      one substrate (§6, Phase 11).
- **Q1: Buildings = a high-level profile** that lowers to substrate ops; keeps IFC
      + room-graph generator (§6, Phase 11).
- **Q2: Invest in a generative persistent-name layer**, phased, **with a spike in
      the spine** (bucket 0.5) before Phase 4 hardens it (§2).
- **Q3: Expression model:** HOCON carries refs + arithmetic + **registered-function
      calls**; all logic stays in code (§1, Phase 0).
- **Q4: Selector grammar:** SQL-`WHERE`-style predicate over a **versioned
      element-attribute model**; `lark` parser, escalate to CEL only if needed (§2).
- **Q5: Solver licensing: copyleft accepted** (settled, no longer open) >> use
      SolveSpace/`py-slvs` + Ondsel; the engine is **GPL** (§8, §15).
- **Q6: Versioning:** per-domain `schema_version` + migration converters + upgrade
      prompt; kernel bump invalidates cached geometry, definitions migrate (§14).
- **Q7: PartCAD & friends as plugin converters**, not core (§14, Phase 13).
- **Scope: CAD + kinematics proven first; CAM & PCB seamed now, built late**
      (design §0/§6a/§6b, Phases 15–16); FEA/CFD stays out (§17).
- **Determinism: equality = topology signature + toleranced measures** (not BREP
      bytes); cache key = subtree hash + pinned kernel version (design §4a, bucket 0.4).
- **Plan shape: thin vertical slices (buckets)**: every bucket ends at
      author>>build>>view/export with a demo + gate.
- **v1 reuse framed honestly:** spec/IO + viewer + patterns carry over; the general
      kernel/refs/ops/executor are greenfield (see "Where we are").

**Resolved by research this revision** (findings in [`research/`](./research/),
decisions in design §19):

- **Direct-modeling ceiling:** v1 = well-behaved-topology face ops only, refuse
      out-of-envelope, dual validity gate; auto-maintained relations excluded `(A)`
      (Phase 4 + spike bucket 4.0).
- **Class A:** ship the **G2** engineering subset + self-built curvature/zebra
      analysis; true Class A out of scope (Phase 9).
- **MBD depth:** rigid bodies + gravity + springs/dampers + simple contact;
      flexible/friction-rich/continuous contact excluded (Phase 14).
- **CAM kernel:** build 2.5D+drilling on **OCCT sections + Clipper2/`pyclipr`**,
      generic post in-house; **opencamlib** = optional 3D plugin; 5-axis out (Phase 15).
- **PCB ownership:** own data model + geometric DRC + 3D lowering; delegate
      routing/fab to **KiCad** via `.kicad_pcb` round-trip; export **STEP AP214**
      (Phase 16).
- **Building altitude:** stays a thin lowering to substrate ops; no sub-substrate.
- **Provenance-map budget:** O(part-topology), lazy for imports, enforced Phase 12/14.

**Still open (empirical / spike-gated)**, direction decided, magnitude unknown:

- [ ] Direct-modeling **success rate** on real dirty imports (Phase 4 spike; biggest
      geometry risk)
- [ ] G2 fill/blend **robustness** on non-trivial surfaces (surfacing spike)
- [ ] Provenance-map budget at large-assembly scale (Phase 12 measures)
- [ ] `.kicad_pcb` **write** round-trip fidelity (likeliest PCB integration risk)
- [ ] MBD contact fidelity useful before it becomes a physics engine (revisit vs real
      mechanisms)
