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
