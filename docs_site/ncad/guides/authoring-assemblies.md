# Authoring assemblies

An **assembly** places instances of parts and constrains how they sit together. Extension:
`.asm.hocon`. Built with `ncad assemble`. Validated against `schema/assembly_schema.hocon`.

```properties
units = mm
assembly {
  instances = [ ... ]      # placed copies of parts / sub-assemblies
  constraints = [ ... ]    # mates (typed relations between connectors)
  joints = [ ... ]         # lower-pair joints (DoF-bearing)
  couplings = [ ... ]      # relations that make joints follow each other
  expected_contact = [ ... ] # by-design touches to skip in interference
}
```

## Instances

Each instance is a placed copy, referenced elsewhere by its `id`:

```properties
{ id = axle,  file = "caster.hocon", part = axle, lock = true }
{ id = swivel, assembly = "wheel_axle.asm.hocon", placement = { position = [ 0, 0, -28 ] } }
{ id = bolt,  file = "caster.hocon", part = bolt,
  pattern = { kind = circular, count = 4, axis = { point = [0,0,0], dir = [0,0,1] } } }
```

- `file` + `part` instances a part; `assembly` instances a nested sub-assembly (composed as one rigid
  body). `lock = true` grounds an instance as the fixed reference.
- `placement` seats an instance explicitly; otherwise the solver positions it from the constraints.
- `pattern` (linear / circular / table), `mirror` (with `of`), and `replace` compose many instances
  from one.

## Connectors

A **connector** is a named coordinate frame on a part, declared in the part document. Assemblies
refer to connectors by name, never by raw coordinates, so a mate survives a part rebuild. A connector
can be a coordinate (`at_point = [x,y,z], axis = [..]`) or an attribute selector
(`at = "select faces where type = 'cylinder' and max_z < 0"`) or an edge.

## Mates vs joints

Two ways to relate instances:

- **Mates** (`constraints`) are assembly-modeling relations that remove degrees of freedom. Types:
  coincident, mate, flush, align, concentric, parallel, perpendicular, angle, distance, offset, lock,
  tangent, symmetric, width. They lower to normal-form primitives and solve to placements.
- **Joints** (`joints`) are lower pairs that intentionally KEEP degrees of freedom (for motion).
  Types: fixed, revolute, slider, cylindrical, planar, ball, screw, point_on_line, slot,
  constant_velocity, universal-style pairs (cylspherical, revcylindrical, sphspherical, revrevolute),
  and more.

```properties
joints = [
  { id = spin, type = revolute, between = [
    { instance = axle, connector = shaft },
    { instance = wheel, connector = hub } ] }
]
```

The solver reports DoF state (well / under / over / redundant) so you know whether the mechanism is
properly constrained.

## Couplings

A **coupling** ties one joint's motion to another (the basis for geared and cammed mechanisms):
gear, belt, rack_pinion, universal, cam, scotch_yoke, geneva. A `gear` coupling takes a `ratio`; a
`cam` takes a `profile` (a dwell-rise-return object); a `scotch_yoke` an `amplitude`; a `geneva` a
`{slots, crank_radius}` spec. Couplings are what a motion driver propagates through.

## BOM, mass, interference

`ncad assemble` also gives you:

- a **bill of materials** (line items by part, per-unit and total mass, mass-weighted world COG),
- **interference** checks (pairwise clearance/touching/interfering), with an `expected_contact`
  allow-list to skip by-design contacts.

## A complete example

`examples/06-assemblies/caster.asm.hocon` (a swivel caster) exercises a nested sub-assembly, a
circular bolt pattern, a tangent mate, and an edge-derived connector:

```properties
assembly {
  instances = [
    { id = plate, file = "caster.hocon", part = top_plate, lock = true }
    { id = fork,  file = "caster.hocon", part = fork, lock = true }
    { id = swivel, assembly = "wheel_axle.asm.hocon", placement = { position = [ 0, 0, -28 ] } }
    { id = bolt,  file = "caster.hocon", part = bolt,
      pattern = { kind = circular, count = 4, axis = { point = [0,0,0], dir = [0,0,1] } } }
    { id = stop,  file = "caster.hocon", part = stop }
  ]
  constraints = [
    { id = seatStop, type = tangent, between = [
      { instance = stop, connector = face },
      { instance = fork, connector = post } ] }
  ]
}
```

```bash
ncad assemble examples/06-assemblies/caster.asm.hocon && ncad view
```

To make an assembly move, add a motion study: see [authoring motion](authoring-motion.md).
