# gate-5.7: Phase 5 assembly-completeness capstone (swivel caster)

A plate-mount swivel caster, the real recognizable assembly that exercises every bucket 5.7
feature. Built on the real kernel; see `tests/examples/test_gate_5_7.py`.

## Parts (`caster.hocon`)

- `top_plate`: the square mounting plate (bolts to the equipment underside) with a central swivel
  bore. Named connectors: `swivelBore` (the bore cylinder) and `mountEdge` (an EDGE-derived
  connector on the top face).
- `fork`: the swivel yoke hanging below the plate, with a top swivel `post` (concentric into the
  plate bore) and a cross `axleBore` for the wheel axle.
- `wheel`, `axle`: the wheel and its axle pin.
- `bolt`: a mounting bolt, arrayed around the plate bolt circle.
- `stop`: a swivel-limit block whose face seats tangent to the fork post.

## Sub-assembly (`wheel_axle.asm.hocon`)

The wheel pinned to the axle by a revolute joint (free to spin). It is instanced into the caster
as one rigid body.

## Assembly (`caster.asm.hocon`) - the 5.7 feature tour

- **Nested sub-assembly rendering**: the `swivel` instance references `wheel_axle.asm.hocon`; its
  solved instances compose under the caster as `swivel/axle`, `swivel/wheel`.
- **Component pattern**: the `bolt` instance carries a circular `pattern` (count 4), placing
  `bolt/0..bolt/3` on the bolt circle.
- **Tangent mate**: `seatStop` seats the stop's planar face tangent to the fork's cylindrical
  post.
- **Edge-derived connector**: the plate's `mountEdge` is a named frame on a top-face edge.

The plate is grounded (`lock`); the fork's post is `connect`-snapped concentric to the plate bore.
The assembly builds with no issues, rolls up a BOM + mass, computes interference, and writes a
structured STEP AP242. Coupling enforcement and time-varying motion are Phase 6.
