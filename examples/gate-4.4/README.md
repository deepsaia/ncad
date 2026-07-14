# gate-4.4: Phase 4 completeness capstone parts

Real, recognizable parts exercising the bucket 4.4 features (persistent-name / direct-modeling /
relational completeness). Each builds on the real kernel; see `tests/examples/test_gate_4_4.py`.

## `mounting_cover.hocon`

A round gearbox / pump end cap: a d140 x 10 aluminium plate with a central pilot bore and SIX
counterbored bolt holes on a d100 bolt circle. The counterbore cutter (a d9 through shaft fused
to a d15 x 5 counterbore head) is built ONCE, then a **feature pattern** replays that cut at six
circular positions about the axis. This is the NX/Creo/Fusion "pattern feature": pattern the
cut's effect, not a body. The cutter is built before the plate so the plate is the running solid
the feature pattern acts on (feature-ordering rule 12e).

## `mirrored_hinge.hocon`

A door hinge leaf with a knuckle bore and a separate pin. Exercises three 4.4 features:
- **feature_mirror**: a reinforcing strap boss on the +y half is mirrored across the XZ plane to
  the -y half (one authored boss, symmetric result).
- a keep-separate union produces a two-body part (leaf + pin).
- **relate moving_body**: the pin body is moved COAXIAL to the knuckle bore so it seats in the
  hinge (a two-body assembly-in-a-part; the pin aligns, it is not fused).

## `curved_import_edit.hocon`

Import a foreign solid whose outline has a freeform (spline) side, then PROJECT that curved top
edge into a new sketch as construction reference geometry and cut a locating slot beside it.
Exercises **curved-edge projection** on imported geometry: the spline edge OCCT hands back is
sampled into an interpolated construction spline (before 4.4 the kernel refused a spline edge).
The `file` points at `out/curved_import_edit_input.step`, which the test exports from our own
kernel first (no committed binary; reproducibility). Persistent names survive a rebuild.
