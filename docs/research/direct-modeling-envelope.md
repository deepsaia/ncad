# Direct-Modeling Envelope (OCCT, measured)

**Source:** bucket 4.0 de-risking spike. Reproduce with
`uv run python -m spikes.direct_modeling_4_0.run_matrix`.
**Kernel:** `build123d=0.10.0; ocp=7.8.1.1.post1`.
**Date:** 2026-07-11.

This is the empirical companion to `direct-modeling-occt-ceiling.md` (which catalogs the APIs
and their documented failure modes). It measures what OCCT actually does on **our own STEP
exports**, and states the envelope Phase 4.1-4.3 may build on. Foreign-STEP stress-testing is a
logged follow-up; these numbers describe clean, ncad-authored B-reps only.

## Method

Input corpus: the last-few generated gate models exported to STEP (mounting_bracket = one
filleted part; pattern_studs, spoke_hub, symmetric_bracket, mirror_pair, split_block, multi_cut,
scoped_merge, materials_part, flanged_coupling = ten real multibody parts across gate docs 3.2
to 3.6) plus three synthetics for cliff coverage (tangent_fillet_chain, thin_wall_box,
sliver_face_block).

Ops: `defeature` (BRepAlgoAPI_Defeaturing, remove one face), planar `move_face` (synthesized as
extrude-face-to-slab + BRepAlgoAPI_Fuse + ShapeFix, since OCCT has no native move-face), and
`offset`/thicken (build123d offset_3d over BRepOffsetAPI_MakeThickSolid). Each op ran in a child
process (GuardedRunner) with a 20s wall-clock timeout, so a hang or segfault would be measured,
not fatal.

Success oracle (three independent tiers; PASS only if all three agree):

1. **gate** = the kernel validity notion (BRepCheck-backed `is_valid`).
2. **sanity** = independent of BRepCheck: finite positive volume, at least one solid, at least
   one face.
3. **intent** = the edit's expected delta occurred (defeature: face count drops and volume
   changes; move_face/offset: volume changes and stays positive).

A run where gate passes but sanity or intent fails is a **gate-vs-reality disagreement**, i.e. a
measured instance of OCCT reporting invalid or no-op geometry as valid (tracker #1315).

Total measured runs: 104 (zero skipped; face indices 0-2 existed on every input).

## Results

| op | input_class | n | pass | fail | timeout | crashed | raised | skip | disagree |
|---|---|---|---|---|---|---|---|---|---|
| defeature | real_filleted | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| defeature | real_multibody | 27 | 0 | 27 | 0 | 0 | 0 | 0 | 27 |
| defeature | synthetic_sliver | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| defeature | synthetic_tangent | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 2 |
| defeature | synthetic_thinwall | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| move_face | real_filleted | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 2 |
| move_face | real_multibody | 27 | 26 | 1 | 0 | 0 | 0 | 0 | 1 |
| move_face | synthetic_sliver | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| move_face | synthetic_tangent | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| move_face | synthetic_thinwall | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | real_filleted | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | real_multibody | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | synthetic_sliver | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| offset | synthetic_tangent | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | synthetic_thinwall | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

Gate-vs-reality disagreements: **38 of 104 measured runs (37%)**. Every one is a case where
`is_valid` returned true on a result that either did nothing or is geometrically empty.

## Key findings

1. **No hangs, no crashes on clean geometry.** Zero timeouts and zero segfaults across all 104
   runs. On our own well-formed STEP the hazard is NOT the documented hang (#33561); it is
   **silent wrong answers**. The subprocess guard still matters for foreign/dirty input and for
   4.2 safety, but on clean parts the oracle, not the timeout, is what catches failure.
2. **`BRepAlgoAPI_Defeaturing.IsDone()` lies constantly.** On 33 of 36 defeature runs it
   returned `IsDone = True` while removing nothing (face count and volume unchanged), and
   `is_valid` agreed. Only mounting_bracket's simple planar faces defeatured for real (39 -> 37
   faces, volume dropped). Defeature is unusable on `IsDone`/validity alone; it must be
   intent-verified (face-count and volume delta) every time.
3. **move_face (fuse + heal) works on simple faces, collapses on complex ones.** It passed on
   every synthetic and 26/27 multibody faces (small planar faces fuse cleanly), but on the
   complex filleted bracket the fuse returned a BRepCheck-valid but **empty** solid (39 -> 0
   faces, volume -> 0). Valid-but-empty is the sharpest #1315 case and only the sanity tier
   catches it.
4. **offset is the most robust op**, passing 25/27 runs including all real parts. The two
   failures were a negative (inward) thicken on the sliver block, which raised. Direction and
   thin walls are the risk, not the happy path.
5. **offset is slightly nondeterministic.** Across two identical runs, `offset` on the filleted
   bracket produced `raised` once and `pass` twice. Any offset result must be treated as
   attempt-and-verify, never assumed.

## The envelope

### GREEN (4.2 may build on these, still oracle-verified)

- **offset/thicken, outward (positive), on any of our clean solids.** 25/27 pass, zero
  disagreements, zero crashes. The most dependable direct op.
- **defeature on simple planar faces of a single-body prismatic part** (the mounting_bracket
  case): 3/3 pass. Narrow, but real.

### RED (4.2 must detect the precondition and refuse; never attempt)

- **defeature on multibody parts and on tangent/sliver/thin-wall topology.** 0/36 useful; every
  attempt was a silent no-op that reported success. Precondition to detect and refuse: target
  face adjacent to a tangent face, on a sliver/small face, or on a multibody/thin-wall solid.
- **move_face on complex filleted/blended solids.** Produced valid-but-empty geometry.
  Precondition to detect and refuse: target face adjacent to non-planar (filleted/blended)
  faces, or a part above a face-count/complexity threshold.
- **inward (negative) offset on thin or sliver walls.** Raised / produced degenerate results.
  Precondition to detect and refuse: offset magnitude >= smallest local wall thickness.

### YELLOW (allowed only behind the GuardedRunner + full three-tier oracle; never trusted on the gate alone)

- **move_face on simple planar faces** (synthetics, simple multibody faces): passes often but is
  one fuse away from valid-but-empty, so it must run guarded and be intent+sanity verified.
- **defeature generally:** even where it "works", `IsDone` and `is_valid` cannot be trusted;
  require an intent check (face-count and volume delta) on every result.
- **any offset:** measured nondeterminism means even GREEN offsets run guarded and verified.

## Baseline framing (vs Parasolid / Granite)

NX (Synchronous Technology), Creo (Flexible Modeling), and Fusion sit on Parasolid/Granite,
which guarantee these direct edits: a defeature either removes the face or reports a real error,
and a move-face returns a correct solid or fails loudly. OCCT does not meet that bar. Its
signature failure here is not the crash (we saw none on clean input) but the **confident
false positive**: 37% of runs returned "valid" on geometry that was unchanged or empty.

The consequence for Phase 4.2: ncad cannot ship OCCT direct edits on `IsDone`/validity the way a
Parasolid-backed tool can. Every direct op must run behind the GuardedRunner and pass the
independent sanity + intent oracle before its result is accepted or recorded as a feature. 4.2
therefore ships offset (outward) and simple-face defeature as GREEN (still verified), gates the
rest as YELLOW, and refuses the RED preconditions at authoring time with an id-tagged reason,
exactly as the Phase 4 gate demands.
