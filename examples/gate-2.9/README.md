# gate-2.9: Phase 2 capstone (mounting bracket)

`mounting_bracket.hocon` composes the Phase 2 op vocabulary into one coherent part and is
the Phase 2 gate: it builds deterministically (same spec >> identical geometry signature,
design section 4a) and round-trips to STEP. See `tests/examples/test_gate_examples.py` for
the build-twice determinism check, the golden-signature match, and the STEP round-trip.

## The part (9 ops)

extruded base plate >> shell (open bottom) >> fillet the base corners >> revolved cylindrical
boss (unioned on) >> stiffening rib >> counterbored M6 mounting-hole pair >> chamfered boss
rim >> drafted planar sides.

Coverage: extrude / shell / fillet / revolve / boolean / rib / hole-wizard (counterbore +
size+fit) / chamfer (two-distance) / draft, plus sketches (element and constrained open).

## CAD-best-practice feature order (why this order)

The order is not arbitrary; it is what a real modeler would do, and departures produce
invalid geometry or OCCT crashes:

- **Shell early, on the clean plate.** Shelling the fully fused+drilled solid with one
  inward offset self-intersects against the counterbores and boss interior and yields an
  invalid B-rep (BRepCheck fails). Shelling the bare plate first is valid.
- **Fillet the base corners before the boss/holes.** A late fillet on the complex
  fused+drilled+shelled solid segfaults OCCT; filleting the simple shelled plate's vertical
  corners is robust.
- **Dress-up (chamfer, draft) last**, on the finished solid.

## Substitutions and limitations (real, not simplifications)

- **"variable fillet" >> constant fillet + a two-distance chamfer.** Variable-radius fillet
  was deferred in bucket 2.6; the capstone uses a constant `fillet` plus a two-distance
  `chamfer` on the boss rim.
- **draft applies to planar faces only.** The `vertical` face keyword also selects
  cylindrical walls (fillet rounds, boss, hole bores); draft is undefined on those and OCCT
  rejects them, so `Build123dKernel.draft` filters to planar faces (a bucket-2.9 fix). This
  matches CAD tools, which draft planar walls only.
- **No `wrap` label.** wrap needs a single stable target face, but a boolean/rib/hole stack
  produces only positional face ids (no semantic `cap(+Z)` tag survives a fuse), and
  referencing a positional id would be order-fragile (against the reference-model
  discipline, design section 2). A stable face selector over the attribute model is the
  proper prerequisite; it is deferred. `wrap` is exercised on its own in gate-2.8b.

## Fixes this capstone surfaced

- `revolve` now resolves its `profile` ref (added to the builder `_REF_FIELDS` as an
  `input` role, matching `extrude`/`sweep`); previously the profile ref was ignored and the
  op used the adjacent shape.
- `Build123dKernel.draft` filters selected faces to planar ones (above).
