# gate-2.9: Phase 2 capstone (mounting bracket)

`mounting_bracket.hocon` composes the Phase 2 op vocabulary into one coherent part and is
the Phase 2 gate: it builds deterministically (same spec >> identical geometry signature,
design section 4a) and round-trips to STEP. See `tests/examples/test_gate_examples.py` for
the build-twice determinism check, the golden-signature match, and the STEP round-trip.

## The part (10 ops)

extruded base plate >> fillet the corners >> draft the walls >> shell (open bottom) >>
revolved cylindrical boss (unioned on) >> stiffening rib >> counterbored M6 four-hole
pattern >> chamfered boss rim >> pocket-trim the rib into a tapered gusset.

Coverage: extrude / fillet / draft / shell / revolve / boolean union / rib / hole-wizard
(counterbore + size+fit) / chamfer (two-distance) / pocket, plus sketches.

## CAD-best-practice feature order (why this order)

Order is part of the model's meaning (like a Blender modifier stack). See
`docs/feature-ordering.md` for the full rules. The ones this part relies on:

- **All base dress-up on the clean prism first** (fillet, draft, shell), BEFORE the boss,
  rib, and holes complicate the topology. A late shell yields an invalid B-rep; a late
  fillet segfaults OCCT.
- **Fillet before draft** (draft's taper destroys the strictly-vertical corner edges the
  fillet's `vertical` keyword needs).
- **Draft applies to planar faces only** (the kernel filters non-planar faces).

## Trimming the rib into a gusset (boolean technique)

The `rib` op makes a constant-depth rectangular blade, which overshoots as a tall fin. A
`pocket` (`end = symmetric`, so it cuts through the full rib thickness) removes the
top-outer triangular wedge so the web tapers from the boss down to the plate, leaving a
single clean triangular gusset. This is the boolean-trim technique; the proper fix is a
native rib until-material / trim extent, deferred (see the Phase 2 backlog in
`docs/plan.md`).

## Substitutions

- **"variable fillet" >> constant fillet + a two-distance chamfer** (variable-radius fillet
  was deferred in bucket 2.6).

## Fixes this capstone surfaced

- `revolve` now resolves its `profile` ref (added to the builder `_REF_FIELDS` as an
  `input` role, matching `extrude`/`sweep`); previously the ref was ignored and the op used
  the adjacent shape.
- `Build123dKernel.draft` filters selected faces to planar ones (drafting a cylinder is
  undefined and OCCT rejects it).
- `extrude_kwargs` now rejects a bare `symmetric` / `second_distance` field that does not
  match `end` (the end-condition is chosen by `end = symmetric` / `end = two_side`).
  Previously a stray `symmetric = true` was silently dropped, building a one-sided extrude -
  which is exactly what left the rib half-trimmed (a square + triangle) until this fix.
