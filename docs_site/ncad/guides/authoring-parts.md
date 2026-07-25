# Authoring parts

A **part** is the base document kind: a `parts {}` block where each named part is an ordered feature
tree. Extension: `.hocon` or `.json`. Built with `ncad build`. Validated against
`schema/part_schema.hocon`.

```properties
units = mm
parts {
  <name> {
    profile = solid            # solid | sheet
    material = steel_1018      # resolves from the material library
    connectors = [ ... ]       # named coordinate frames for assemblies (optional)
    features = [ ... ]         # the ORDERED feature tree
  }
}
```

Order is the model's meaning: each feature consumes the previous op's result and its topology, like a
modifier stack. OpenCASCADE is order-sensitive, so a late shell or fillet can fail on geometry that a
different order would accept; see [feature ordering](https://github.com/deepsaia/ncad/blob/main/docs/feature-ordering.md).

## Sketches

A sketch places 2D geometry on a plane (`XY`, `YZ`, `XZ`, or a datum) and solves it with a constraint
solver. Two authoring styles:

- **`elements`**: high-level shapes that need no solving (rectangle, circle, and sugar like polyline,
  slot, polygon, plus generated profiles gear/cam/geneva/airfoil).
- **`entities` + `constraints`**: primitive geometry (point/line/arc/circle/ellipse/conic/bezier/
  spline) positioned by geometric constraints, for a real driven sketch.

```properties
{ id = sk, op = sketch, plane = XY,
  elements = [ { id = r, type = rectangle, w = 60, h = 40 } ] }
```

Constraint types include: horizontal, vertical, coincident, distance, radius, diameter, parallel,
perpendicular, equal, symmetric, midpoint, point_on, collinear, concentric, tangent (G1/G2), fix,
angle. An under-constrained sketch is reported (`sketch_underconstrained`), not silently guessed.

## Solid features

The workhorses that turn sketches into solids and dress them:

| Family | Ops | Notes |
| --- | --- | --- |
| Add material | `extrude`, `revolve`, `loft`, `sweep`, `rib` | `rib ... until = true` grows to meet material and auto-trims |
| Dress-up | `fillet`, `chamfer`, `shell`, `draft`, `hole` | `hole size = M8, fit = normal` uses ISO clearance charts |
| Combine | `boolean` (union / cut / common) | multibody-aware; body identity is preserved |
| Multiply | `pattern` (linear / circular), `mirror` | patterns replay the source feature(s) |
| Primitives | `primitive` (box, cylinder, sphere, ...) | blockout modeling for mechanisms and robots |

Selectors pick edges and faces by attribute so a reference survives a rebuild:
`edges = vertical`, or `select faces where type = 'cylinder' and max_z < 0`. This is the
persistent-naming layer; it is why editing an upstream parameter does not break a downstream fillet.

## Direct edits

History-free edits on the current B-rep (or an imported solid): `move_face`, `offset_face`,
`defeature`, `reposition_hole`, and a one-shot planar `relate`. These are guarded by a measured
robustness oracle (a child-process timeout catches OCCT hangs), so a risky edit fails cleanly instead
of crashing. See the [import-edit-export workflow](../workflows/import-edit-export.md).

## Materials, parameters, datums

- `material = <name>` resolves from `materials/seed.hocon`; a document can add or override with an
  inline `materials {}` block or an external `materials_library` file. Material drives mass properties
  and appearance.
- `parameters {}` plus `${...}` expressions make a part parametric (a restricted-AST evaluator:
  literals, refs, arithmetic, registered functions).
- `datums {}` and the `datum_plane` / `datum_axis` ops add reference geometry for downstream features
  and connectors.

## A complete example

`examples/03-dress-up/shelf_bracket.hocon` (walked step by step in
[Build your first part](../getting-started/first-part.md)) combines a sketch, an extrude, a boolean
union, a rib grown until material, and a datum plane:

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
      { id = gusset, op = rib, profile = gusset_sk, target = ell, thickness = 5, until = true }
      { id = mount_dp, op = datum_plane, method = offset, base = YZ, distance = 30 }
    ]
  }
}
```

```bash
ncad build examples/03-dress-up/shelf_bracket.hocon && ncad view
```

For the full, code-generated list of every op and its parameters, see the
[Operations Reference](../reference/index.md). More part examples live under
`examples/02-solid-features`, `examples/04-patterns-multibody`, and `examples/05-direct-modeling`.
