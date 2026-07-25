# Reference: authoring analyses (FEA)

A structural finite-element load case on a part. Extension `.analysis.hocon`. Run with
`ncad analyze <doc>`. ncad owns the model (mesh, load case, result read-back) and delegates the solve
to CalculiX (`ccx`), which is not bundled. Without the solver, the run reports `skipped` and the load
case still validates.

## Top-level shape

```properties
analysis {
  part = "<part>.hocon"
  mesh { element_size = 3.0, order = 2 }     # order 1 linear (C3D4) / 2 quadratic (C3D10)
  constraints = [ ... ]                       # boundary conditions
  loads = [ ... ]                             # applied loads
  steps = [ ... ]                             # analysis steps (procedures)
}
```

## Vocabulary

- **constraints**: boundary conditions on selected faces. `type = "encastre"` fully fixes a face.
  Faces are picked by keyword: `top`, `bottom`, `all`, `vertical`, `horizontal`.
- **loads**: `pressure` (magnitude in Pa), `gravity` (`g` + `direction`) for structural steps;
  `flux`, `film` for thermal steps.
- **steps / procedures**: `static` (linear stress + displacement, von Mises derived), `frequency`
  (modes / eigenfrequencies), `heat_transfer` (steady or transient thermal).

## Worked example (L-bracket)

```properties
analysis {
  part = "bracket.hocon"
  mesh { element_size = 3.0, order = 2 }
  constraints = [ { name = "base", where = {face = "bottom"}, type = "encastre" } ]
  loads = [
    { name = "tip",    where = {face = "top"}, type = "pressure", magnitude = 2.5e5 }
    { name = "weight", type = "gravity", g = 9.81, direction = [0, 0, -1] }
  ]
  steps = [
    { name = "stress", procedure = "static",    output = {node = ["U", "RF"], element = ["S", "E"]} }
    { name = "modes",  procedure = "frequency", eigenvalues = 6 }
  ]
}
```

```bash
uv sync --extra fea      # gmsh + meshio (mesh + result IO; the ccx solver is separate)
ncad analyze examples/10-fea/bracket.analysis.hocon
```

Writes `out/analyses/<part>/<part>.analysis.json` (peak von Mises, displacement, eigenfrequencies)
plus a field mesh for the viewer's Analyze mode.

## Pitfalls

- **Units are SI**: the deck is in metres, stress in Pa. Geometry authored in mm is scaled for the
  deck automatically.
- **ccx is optional and external.** Without it, `ncad analyze` reports `status = skipped` (not a
  failure). Point `NCAD_CCX` at a `ccx` binary to enable the solve. Report the status honestly.
- Faces are selected by keyword, so the load case survives a part rebuild.

More cases: `examples/10-fea/` (a con-rod, an F1 front wing).
