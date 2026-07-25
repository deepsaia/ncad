# Reference: authoring parts

A part document is a `parts {}` block; each named part is an ordered feature tree. Extension
`.hocon` or `.json`. Build with `ncad build <doc>`.

## Top-level shape

```properties
units = mm
parts {
  <name> {
    profile = solid            # solid | sheet
    material = steel_1018      # resolves from the material library (mass + appearance)
    connectors = [ ... ]       # named coordinate frames for assemblies (optional)
    features = [ ... ]         # the ORDERED feature tree
  }
}
```

Optional top-level: `parameters {}` (+ `${...}` expressions), `datums {}`, inline `materials {}`,
`materials_library = "..."`, `metadata {}`.

## Sketches

Place 2D geometry on a plane (`XY`, `YZ`, `XZ`, or a datum). Two styles:

- `elements`: high-level shapes needing no solve: `rectangle`, `circle`, and sugar `polyline`,
  `slot`, `polygon`, plus generated profiles `gear`, `cam`, `geneva`, `airfoil`.
- `entities` + `constraints`: primitives (`point`, `line`, `arc`, `circle`, `ellipse`,
  `ellipse_arc`, `conic`, `bezier`, spline) positioned by constraints.

Constraint types: horizontal, vertical, coincident, distance, radius, diameter, parallel,
perpendicular, equal, symmetric, midpoint, point_on, collinear, concentric, tangent (g1/g2), fix,
angle, minor_radius, smooth, length_ratio, length_difference, equal_angle, point_line_distance. An
under-constrained sketch is reported (`sketch_underconstrained`), never guessed.

## Solid features

| Family | Ops |
| --- | --- |
| Add material | `extrude`, `revolve`, `loft`, `sweep`, `rib` (`until = true` grows to meet material) |
| Dress-up | `fillet`, `chamfer`, `shell`, `draft`, `hole` (`size = M8, fit = normal/close/loose/tapped`) |
| Combine | `boolean` (`operation = union / cut / common`), multibody-aware |
| Multiply | `pattern` (linear / circular), `mirror` |
| Primitives | `primitive` (`kind = box / cylinder / sphere / ...`) for blockout modeling |
| Direct edits | `move_face`, `offset_face` (or `offset`), `defeature`, `relate`, `reposition_hole` |

Selectors pick topology by attribute: `edges = vertical`, or
`select faces where type = 'cylinder' and max_z < 0`.

## Worked example (shelf bracket)

```properties
units = mm
parts {
  shelf_bracket {
    profile = solid
    material = steel_1018
    features = [
      { id = wall_sk, op = sketch, plane = YZ,
        elements = [ { id = r, type = rectangle, w = 40, h = 60 } ] }
      { id = wall, op = extrude, profile = wall_sk, distance = 6 }
      { id = arm_sk, op = sketch, plane = XY,
        elements = [ { id = ra, type = rectangle, w = 50, h = 40 } ] }
      { id = arm_ext, op = extrude, profile = arm_sk, distance = 6 }
      { id = ell, op = boolean, operation = union, target = wall, tool = arm_ext }
      { id = mount_dp, op = datum_plane, method = offset, base = YZ, distance = 30 }
    ]
  }
}
```

```bash
ncad build examples/03-dress-up/shelf_bracket.hocon && ncad view
```

## Pitfalls

- **Feature order** is part of the meaning; a fillet or shell placed too late can fail on the B-rep.
- **Selectors, not indices**, keep references stable across a parameter edit.
- Report the real diagnostics from `ncad build` / `ncad validate`; do not assume a build succeeded.

More: `examples/02-solid-features`, `examples/04-patterns-multibody`, `examples/05-direct-modeling`;
the full op list is the Operations Reference on the docs site.
