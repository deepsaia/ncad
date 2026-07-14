# Feature ordering: the rules of the pipeline

A part is an **ordered feature tree**: each op consumes the previous op's result (its solid
and its topology) and produces the next. Order is part of the model's meaning, not an
implementation detail - the same set of features in a different order can produce a
different shape, an invalid B-rep, or an OCCT crash. This is the same truth as Blender's
modifier stack and geometry-node graphs: a stateful pipeline where each stage depends on the
exact geometry the previous stage emitted.

This document collects the ordering rules we have learned, the failure mode each one guards
against, and why. **Keep it updated:** when a bucket discovers a new ordering constraint (an
op that must precede/follow another, a selector that breaks after a transform, an OCCT
fragility tied to sequence), add a rule here in the same PR.

---

## The rules

### 1. Dress-up the base while it is a clean prism, before holes and stacked bodies

Do `shell` / `fillet` / `draft` on the simple base solid, BEFORE `boolean`/`revolve`/`rib`
fuse other bodies onto it or `hole` pierces it.

- **Why:** OCCT's offset (shell) and fillet algorithms are robust on simple analytic
  geometry and fragile on complex fused+drilled topology.
- **Failure mode:** a late `shell` on a plate that already carries a boss and counterbores
  self-intersects and returns an invalid B-rep (BRepCheck fails, `_robust` rejects it). A
  late `fillet` on that same stack can **segfault** OCCT (a native crash, not a catchable
  exception).
- **Seen in:** gate-2.9 `mounting_bracket`.

### 2. Fillet before draft

If you both fillet the vertical corners and draft the side walls, fillet FIRST.

- **Why:** our `EdgeSelector` `vertical` keyword matches strictly vertical edges (near-zero
  X/Y direction). `draft` tapers the walls, so after a draft those corner edges are no
  longer vertical and the keyword selects nothing.
- **Failure mode:** draft-then-fillet >> the fillet finds 0 edges and does nothing (or
  errors on an empty set).
- **Seen in:** gate-2.9 `mounting_bracket`.

### 3. Draft applies to planar faces only

`draft` tapers planar walls about a neutral plane; a taper angle is undefined on a cylinder
or sphere. `Build123dKernel.draft` filters the selected faces to planar ones and raises if
none remain.

- **Why:** OCCT `BRepOffsetAPI_DraftAngle` rejects non-planar faces.
- **Failure mode:** feeding a face keyword like `vertical` (which also selects filleted
  cylindrical corners, boss walls, and hole bores) straight to draft raises
  `Standard_Failure`.
- **Guard:** the planar filter lives in the kernel, so every `draft` is protected. Author
  intent still matters - select the walls you mean to draft.
- **Seen in:** gate-2.9 `mounting_bracket` (the kernel filter was added there).

### 4. A body must be a single solid before ops that require one

`draft` (and other whole-body ops) require the running shape to be ONE solid. A `rib` or
`boolean` that does not fully overlap the target can leave two disjoint solids.

- **Why:** OCCT `DraftAngle` errors with "Topological parent must be a single Solid" on a
  multi-solid compound.
- **Failure mode:** a gusset/rib profile that floats outside the body it should brace fuses
  to nothing, leaving 2 solids; the next whole-body op fails.
- **Guard:** author rib/gusset profiles that clearly overlap both bodies they join (start
  inside the boss wall, end inside the plate). Check `len(solid.solids()) == 1` when
  debugging.
- **Seen in:** gate-2.9 `mounting_bracket`.

### 5. `revolve`'s profile is the resolved `profile` ref (not adjacency)

A `revolve` revolves the face named by its `profile` ref and returns a STANDALONE solid;
recombine it with `boolean` `union`. (Before bucket 2.9 `revolve` had no ref entry and
silently used the previous feature's shape by adjacency - fixed by adding
`revolve: {"profile": "input"}` to the builder.)

- **Why:** additive-in-place ops (`rib`, dress-up) modify the running solid; `revolve`
  originates a new body from a profile, like `extrude`.
- **Seen in:** gate-2.9 `mounting_bracket`.

### 6. End-conditions are chosen by `end`, not bare boolean flags

An extrude/pocket end-condition is selected by `end` (`end = symmetric`, `end = two_side`,
`end = through_all`, ...), NOT by an intuitive bare flag like `symmetric = true`.
`extrude_kwargs` now REJECTS a stray `symmetric`/`second_distance` field that does not match
`end`.

- **Why:** before bucket 2.9 a bare `symmetric = true` was silently dropped, so a pocket
  meant to cut symmetrically through a rib only cut one side - leaving a half-trimmed rib
  (a square + a triangle) that looked like two ribs.
- **Failure mode:** silent wrong geometry (the worst kind - it builds and validates, just
  not what you asked for). Now it raises `ExtrudeParamError`.
- **Seen in:** gate-2.9 `mounting_bracket` (the gusset trim).

### 7. `pattern` replicates the running result, so place it after the geometry it copies

`pattern` (feature-level, linear/circular) copies the whole running body/bodies at each
placement. Put it AFTER the feature(s) whose geometry you want replicated. It can change the
running shape's cardinality: `merge = false` emits a multi-body `BodySet`, so every op after
it sees several bodies (per-body dispatch is the `scope` field's job, 3.4).

- **Why:** body pattern copies POSITIVE material well; it does NOT reproduce a cut/hole
  array (fusing rotated copies fills the holes back in) - that is feature pattern, deferred.
- **Failure mode:** a `merge = true` pattern of disjoint copies fuses to a multi-solid
  compound, not one solid; if a single solid is required, ensure the copies overlap (or keep
  `merge = false` and treat the result as a multibody part).
- **Seen in:** gate-3.2 `patterned_bodies` (`spoke_hub` overlaps at the axis to fuse to one
  solid; `pattern_studs` keeps 12 separate bodies).

### 8. `mirror` reflects the running result, so place it after the geometry to reflect

`mirror` reflects the whole running body/bodies across a plane. Put it AFTER the feature(s)
whose geometry you want reflected. Like `pattern`, it can change cardinality: `merge = false`
emits a multi-body `BodySet` (original + reflection), so every op after it sees two bodies
(per-body dispatch is the `scope` field's job, 3.4).

- **Why:** the default (`keep = true, merge = true`) fuses the original with its reflection.
  If the original TOUCHES the mirror plane (a true half-model), the fused result is one clean
  solid; if it is offset from the plane, fusing yields two disjoint lumps in one compound -
  the same caveat as pattern's fuse-of-disjoint-copies.
- **Failure mode:** a `merge = true` mirror of a plane-offset body is a multi-solid compound,
  not one solid. Put the body on the plane for a fused symmetric part, or use `merge = false`
  and treat the result as a multibody part.
- **Seen in:** gate-3.3 `mirrored_bodies` (`symmetric_bracket` touches YZ and fuses to one
  solid; `mirror_pair` is offset and kept separate as 2 bodies).

### 9. `split` raises body cardinality; `boolean` scope mode needs a prior multibody producer

`split` (keep=both) turns one running body into two; `boolean` scope mode operates on the
bodies of the running multibody shape, addressed by born-once id.

- **Why:** scope mode references bodies by id (`row/body/0`), so it MUST follow a feature that
  minted those ids (a pattern/mirror/split with merge=false, or a prior scoped op). A scope id
  that does not exist in the running shape is a hard error, not a silent no-op, so a typo or a
  stale id after a tree edit is caught.
- **Failure mode:** placing a scope-mode `boolean` before any multibody producer (running
  shape is a single body) errors if more than one id is named; a scope id absent from the
  running BodySet errors. Fix the order or the id, do not drop the op.
- **Seen in:** gate-3.4 `multibody_algebra` (`scoped_merge` unions `row/body/0`+`row/body/2`
  after the pattern mints them; `split_block` splits one body into two).

### 10. Authored order is the tie-breaker; the running solid is the last SOLID, not the last feature

Implicit-input ops (`pattern`, `transform`, `mirror`, `split`, `wrap`) consume the
authored-previous *running solid*, not an explicitly named ref. Two guarantees make that
well-defined, and both are enforced by the executor (not left to chance):

- **The rebuild sort is authored-stable.** Among features whose dependencies are all satisfied,
  the earliest-authored one runs first. A dependency can force a feature EARLIER, but two
  independent features never reorder past each other. Without this, an independent later solid
  could be scheduled before a `pattern`, so the pattern would replicate the wrong body.
- **The running solid skips non-solid features.** A `sketch` produces a face, not a body, so it
  never becomes the running solid an implicit-input op inherits (mirrors the dependency graph's
  `previous_solid`). Otherwise an op right after a sketch grabs the face as its base.

- **Failure mode (before the fix):** a `pattern` authored after `stud` but with a later
  independent `boss` replicated the boss (unstable sort ran `boss` first); a `wrap` right after
  its profile sketch grabbed the sketch face as its base solid.
- **Seen in:** the spaced multibody parts (pattern of studs + a separate boss) and gate-2.8b
  `embossed_logo` (wrap after a marker sketch).

### 11. A datum-referencing op must come after the datum it names

A `sketch` on a datum plane, or a `revolve`/`groove` about a datum axis, references the datum
via `datums.<id>`. The datum feature (`datum_plane` / `datum_axis`) must appear earlier in the
tree so its geometry exists when the reference resolves.

- **Why:** datums are non-solid reference features recorded into the element map; the resolver
  looks up the datum's stored shape by feature id at build time.
- **Failure mode:** a sketch that names `datums.d` before `d` is authored fails resolution
  with an id-attributed "unresolved semantic reference" issue (skip-and-suppress).
- **Note:** datums are non-solid (like `sketch`), so they never become the running solid, and
  the part's built shape is the last SOLID feature (rule 10), never a trailing datum.
- **Seen in:** gate-2.10 `cast_bracket` (a sketch/feature on a datum plane).

### 12. An until-material rib needs its target faces present (place it after the walls it grows to)

An until-material rib (`until = true`) grows its blade until it meets the target solid's faces
(auto-trimmed), replacing the manual boolean-trim workaround. The faces it grows to must exist
when the rib runs.

- **Why:** the blade is extruded with an until/target extent against the running solid; if the
  bracing walls are not there yet, there is nothing to grow to.
- **Failure mode:** an until rib authored before its adjacent walls grows no material and is
  refused ("until-material rib grew no material toward the target").
- **Seen in:** gate-2.10 `cast_bracket` (an until-material gusset rib after both walls).

---

### 12b. A modeled thread comes after the stud/bore it threads

The `thread` op cuts a helical groove on the running solid about an axis. The cylindrical
stud (external) or bore (internal) it threads must already exist, and any dress-up on the
threaded region should precede the thread (a fillet/chamfer after a modeled thread hits the
thousands of thread edges and is slow/fragile).

- **Why:** the thread tool is booleaned with the running solid; there must be a cylinder to
  groove, and OCCT dress-up on a threaded surface is fragile.
- **Failure mode:** threading before the stud exists grooves nothing; filleting after a
  thread can segfault/hang on the thread crest edges.
- **Seen in:** gate-2.10 `hex_bolt` (thread after the shank, dress-up before).

### 13. Direct-edit ops (`defeature`, `offset`) come AFTER the geometry they act on

Direct/synchronous ops edit the *current* B-rep in place (design section 3): they consume the
running solid and reference a baked face by persistent name (4.1), so they must be authored
AFTER every history feature that builds the topology they touch. A `defeature` that removes a
boss top must come after the `boolean union` that creates the boss; an `offset` thickens
whatever solid precedes it.

Two order-sensitive facts, both from the measured 4.0 envelope (`docs/research/
direct-modeling-envelope.md`), enforced by the DirectEditGuard before the kernel op runs:

- **defeature needs a simple planar face on a single-body solid.** Placed before a `boolean`
  that would fuse a second body, the solid is single-body and the target is clean; placed after,
  a multibody solid is refused. Removing a face that is tangent-adjacent to a fillet is refused,
  so a `defeature` must precede a `fillet` that would make its target tangent (or target a
  non-tangent face).
- **inward `offset` is refused once walls get thin.** An inward offset authored after a `shell`
  or a thinning feature can exceed the remaining wall and is refused; keep inward offsets before
  wall-thinning, or offset outward.

- **inward `offset` is refused once walls get thin.** An inward offset authored after a `shell`
  or a thinning feature can exceed the remaining wall and is refused; keep inward offsets before
  wall-thinning, or offset outward.
- **`move_face` (4.2b) is refused when a neighbour is non-planar, or inward past the wall.** The
  fuse/cut synthesis goes valid-but-empty next to a fillet/blend (envelope RED), so a `move_face`
  on a face must come BEFORE a `fillet`/`chamfer` that would round its neighbours; and an inward
  `move_face` past the min wall thickness is refused (place before wall-thinning). See the
  envelope doc.
- **`relate` (4.3a/b) is one-shot: it moves the running body once and does NOT re-solve.** A
  `relate` (planar parallel/coplanar/perpendicular/symmetric, or coaxial/tangent) must come AFTER
  the features that build both the moving body and the geometry the reference belongs to. The
  coaxial/tangent variants (4.3b) need a CYLINDRICAL reference face, so they must follow the
  feature that creates that round face. It applies a rigid transform at build time and is not
  maintained if upstream geometry later changes (maintained relations are Phase 5 assembly mates,
  not direct editing).

- **Failure mode:** a `defeature` on a plain prism face is a silent OCCT no-op (the oracle
  rejects it); the robust target is a face whose removal genuinely changes the solid (a boss top
  that heals back to the base). A `defeature` after a `fillet` that made its target tangent is
  refused by the guard rather than silently corrupting. A `move_face` authored after a `fillet`
  that rounded its neighbour is refused for the same reason.
- **Seen in:** gate-4.2 `defeatured_block` (boss unioned, then its top defeatured) and
  `offset_shell` (base, then outward offset); gate-4.2b `imported_edit` (import, then offset).

### 12. Assembly mates (5.2) solve AFTER every instance's connectors resolve; grounding is required

This is an ASSEMBLY-document rule (an `.asm.hocon` orchestrating parts), not a per-part feature
rule, but the same order-sensitivity applies. The constraint solve (`MateSolver`) needs every
instance's connector frames already resolved (a mate references two connectors), so connector
resolution runs for all instances before the solve. The solve also needs an anchor: the first
instance is grounded by default, plus any `lock = true` instance or `lock` mate. A network with no
grounded body still solves (the first instance pins it) but a truly unconstrained instance keeps
its seed pose (from `connect`/`placement`) and reports free DoF rather than erroring.

- **Failure mode:** a mate referencing a connector that does not resolve (bad selector, wrong part)
  is an id-attributed issue and that mate is dropped; the rest of the network still solves (partial
  assembly stays viewable). An over-constrained network reports its failing mate ids (py-slvs
  `Failed`), it does not silently relax.
- **Seed vs solve:** `connect` (5.1) and `placement` (5.0) set the solver's initial guess; a mate
  network refines from there. `connect` remains single-pass (its target must be an earlier,
  already-placed instance); the solved `constraints[]` network has no such ordering requirement
  among the mates themselves (py-slvs solves them together).
- **Seen in:** gate-5.2 `arm_linkage` (bracket grounded via `lock`, lever mated concentric +
  coincident onto it).

---

## How to work when order bites you

1. Build on the REAL kernel (`DocumentBuilder(Build123dKernel()).build_file(..., formats=
   ("step",))`) - the FakeKernel is analytic and will not reproduce OCCT ordering failures.
2. Bisect: build the feature list truncated to the first N features until it fails; the
   first failing N is the culprit op in its current position.
3. Ask "what would a machinist/modeler do?" - the robust order is almost always the
   real-world manufacturing order (rough stock >> dress-up >> features), because that is the
   topology OCCT's algorithms were tuned for.
4. Fix the ORDER or the geometry; do not delete the op to make the gate green (that hides
   the failure). If an op genuinely does not belong on a part, say so with a reason.
5. Add the rule you learned to this document in the same PR.

## Related

- `docs/design.md` section 4a (equality by topology signature + toleranced measures) - why a
  reordered build that changes topology is a different model.
- The `_robust` wrapper in `build123d_kernel.py` converts OCCT invalid-result failures into
  typed, id-attributed issues; it cannot catch a segfault, which is why order (rule 1)
  matters rather than relying on the gate to reject bad geometry.
