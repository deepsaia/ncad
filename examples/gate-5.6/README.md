# gate-5.6: Phase 5 capstone (revolute-mated assembly >> interference + BOM + STEP AP242)

This is the Phase 5 gate. `mated_bracket.asm.hocon` instances two distinct parts from
`mated_bracket.hocon` (a bored steel bracket + an aluminium lever pin), grounds the bracket,
and joins the lever's hub to the bracket's pivot bore with a **revolute** joint (free to
rotate about Z). Assembling it exercises the whole Phase 5 spine at once: connectors >>
joint lowering + signature >> py-slvs solve >> interference >> BOM + roll-up mass >>
structured STEP AP242 export. See `tests/examples/test_gate_5_6_capstone.py`.

## The gate (design section 7/9/14, plan Phase 5 gate)

> "A two-part mated assembly with one revolute joint exports as structured STEP (AP242) and
> opens in FreeCAD; interference check is correct."

What the slow test asserts:

- **Joint:** `j1` lowers to a `revolute` with signature `[{motion: rotation, axis: Z}]` (the
  freedom Phase 6 will drive).
- **Interference is correct:** the d=12 pin passes through the d=14 bore with radial
  clearance, so the base/arm pair reads **clearance** (pin THROUGH a hole shares no volume
  with the bracket). This is why the bracket is bored (a `boolean cut`, not a solid disk):
  it is a realistic revolute and it makes the interference answer nontrivial.
- **BOM:** two distinct parts (`bracket`, `lever`), quantity 1 each, each with a roll-up
  mass; the assembly has a total mass > 0.
- **STEP AP242:** the exported `.step` round-trips through the OCCT XCAF reader as a
  **2-component assembly tree** (not a flat blob).

## Opens in FreeCAD (manual verification)

The "opens in FreeCAD" half of the gate is a **manual step** (FreeCAD is not a test
dependency). To verify by hand: assemble the example (`ncad assemble examples/gate-5.6/
mated_bracket.asm.hocon <out>`), then open the resulting `mated_bracket.step` in FreeCAD and
confirm it loads as an assembly with two named/colored components (bracket + lever) in the
model tree. The automated round-trip test covers the assembly STRUCTURE; component-NAME
transfer through OCCT's STEP reader is version-fragile on real B-rep, so names are asserted
at the kernel-test level (`test_kernel_export_assembly`), not here.

## Why the pin is bored through, not seated in solid

An earlier draft used `extrude ... cut = true` to bore the bracket, which is **not a valid
op** (the flag is silently ignored, leaving a floating cylinder instead of subtracting) and
made the pair read as a CLASH. The correct pattern is a two-step boolean: extrude the bore
tool, then `op = boolean, operation = cut, target = disk, tool = hole_tool`. This surfaced
the same latent non-op in gate-5.4b, which was fixed alongside.
