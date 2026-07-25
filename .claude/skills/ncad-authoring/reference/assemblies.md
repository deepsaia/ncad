# Reference: authoring assemblies

An assembly places instances of parts and constrains how they sit together. Extension `.asm.hocon`.
Build with `ncad assemble <doc>`.

## Top-level shape

```properties
units = mm
assembly {
  instances = [ ... ]         # placed copies of parts / sub-assemblies
  constraints = [ ... ]       # mates (typed relations between connectors)
  joints = [ ... ]            # lower-pair joints (keep degrees of freedom)
  couplings = [ ... ]         # relations that make joints follow each other
  expected_contact = [ ... ]  # by-design touches to skip in interference
}
```

## Instances

```properties
{ id = axle,  file = "caster.hocon", part = axle, lock = true }
{ id = swivel, assembly = "wheel_axle.asm.hocon", placement = { position = [ 0, 0, -28 ] } }
{ id = bolt,  file = "caster.hocon", part = bolt,
  pattern = { kind = circular, count = 4, axis = { point = [0,0,0], dir = [0,0,1] } } }
```

- `file` + `part` instances a part; `assembly` instances a nested sub-assembly (one rigid body).
- `lock = true` grounds an instance as the fixed reference; `placement` seats it explicitly.
- `pattern` (linear / circular / table), `mirror` (with `of`), `replace` compose many from one.

## Connectors

A connector is a named coordinate frame on a part (declared in the part). Reference it by name, not
raw coordinates, so a mate survives a part rebuild. A connector is a coordinate
(`at_point = [x,y,z], axis = [..]`), an attribute selector
(`at = "select faces where type = 'cylinder' and max_z < 0"`), or an edge.

## Mates vs joints

- **Mates** (`constraints`) remove DoF. Types: `coincident`, `mate`, `flush`, `align`, `concentric`,
  `parallel`, `perpendicular`, `angle`, `distance`, `offset`, `lock`, `tangent`, `symmetric`,
  `width`.
- **Joints** (`joints`) intentionally keep DoF (for motion). Types: `fixed`, `revolute`, `slider`,
  `cylindrical`, `planar`, `ball`, `point_on_line`, `slot`, `screw`, `point_in_line`,
  `point_in_plane`, `in_line`, `line_in_plane`, `in_plane`, `cylspherical`, `revcylindrical`,
  `sphspherical`, `revrevolute`, `no_rotation`, `parallel_axes`, `perpendicular`,
  `constant_velocity`, `at_point`.

```properties
joints = [
  { id = spin, type = revolute, between = [
    { instance = axle, connector = shaft },
    { instance = wheel, connector = hub } ] }
]
```

The solver reports DoF state (well / under / over / redundant).

## Couplings

Tie one joint's motion to another: `gear` (ratio), `belt`, `rack_pinion`, `universal`, `cam`
(profile), `scotch_yoke` (amplitude), `geneva` ({slots, crank_radius}).

## Worked example (wheel + axle)

```properties
units = mm
assembly {
  instances = [
    { id = axle, file = "caster.hocon", part = axle, lock = true }
    { id = wheel, file = "caster.hocon", part = wheel }
  ]
  joints = [
    { id = spin, type = revolute, between = [
      { instance = axle, connector = shaft },
      { instance = wheel, connector = hub } ] }
  ]
}
```

```bash
ncad assemble examples/06-assemblies/wheel_axle.asm.hocon && ncad view
```

## Pitfalls

- `lock` at least one instance, or the whole assembly is free to float.
- Reference connectors by name; do not hard-code placements unless seating a fixed instance.
- `ncad assemble` also gives a BOM, rolled-up mass, and interference (use `expected_contact` for
  by-design touches). Report the reported DoF state; do not assume it solved well.

To make the assembly move, add a motion study (see `motion.md`). Richer example:
`examples/06-assemblies/caster.asm.hocon`.
