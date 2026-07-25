# Authoring analyses (FEA)

An **analysis** is a structural finite-element load case. Extension: `.analysis.hocon`. Run with
`ncad analyze`. Validated against `schema/analysis_schema.hocon`. It is an overlay on a part: ncad
owns the model (mesh, load case, result read-back) and delegates the solve to CalculiX (`ccx`), which
is never bundled. Without the solver installed, `ncad analyze` degrades to a `skipped` status rather
than failing.

```properties
analysis {
  part = "<part>.hocon"
  mesh { element_size = 3.0, order = 2 }     # order 2 = quadratic tets (C3D10)
  constraints = [ ... ]                       # boundary conditions
  loads = [ ... ]                             # applied loads
  steps = [ ... ]                             # analysis steps (procedures)
}
```

## Mesh, constraints, loads

- **mesh**: `element_size` (mm) and `order` (1 linear / 2 quadratic). Gmsh meshes the part's exported
  STEP into tets.
- **constraints**: boundary conditions on selected faces. `type = "encastre"` fully fixes a face.
  Faces are picked by selector keyword (`top`, `bottom`, `all`, `vertical`, `horizontal`).
- **loads**: `pressure` (magnitude in Pa) and `gravity` (with `g` and `direction`) for structural
  steps; `flux` and `film` for thermal steps.

## Steps and procedures

Each step is a procedure over the model:

| Procedure | What it computes |
| --- | --- |
| `static` | linear static stress and displacement (von Mises derived) |
| `frequency` | natural modes (eigenvalues / eigenfrequencies) |
| `heat_transfer` | steady or transient thermal field |

## A complete example

`examples/10-fea/bracket.analysis.hocon`: static stress under a tip pressure with a fixed base, the
first modes, and a steady thermal step, all in one load case:

```properties
analysis {
  part = "bracket.hocon"
  mesh { element_size = 3.0, order = 2 }
  constraints = [
    { name = "base", where = {face = "bottom"}, type = "encastre" }
  ]
  loads = [
    { name = "tip",    where = {face = "top"}, type = "pressure", magnitude = 2.5e5 }
    { name = "weight", type = "gravity", g = 9.81, direction = [0, 0, -1] }
  ]
  steps = [
    { name = "stress", procedure = "static", output = {node = ["U", "RF"], element = ["S", "E"]} }
    { name = "modes",  procedure = "frequency", eigenvalues = 6 }
    { name = "heat",   procedure = "heat_transfer", state = "steady",
      loads = [
        { name = "in",   where = {face = "top"}, type = "flux", magnitude = 500 }
        { name = "conv", where = {face = "all"}, type = "film", sink = 20, coefficient = 15 }
      ] }
  ]
}
```

## Run it

```bash
uv sync --extra fea         # gmsh + meshio (the ccx solver is separate)
ncad analyze examples/10-fea/bracket.analysis.hocon
```

This meshes the part, composes the CalculiX deck, delegates the solve, and reads the results into
`out/analyses/<part>/<part>.analysis.json` (peak von Mises, displacement, eigenfrequencies) plus a
field mesh for the viewer's Analyze mode. The units are SI: the deck is in metres, stress in Pa. If
`ccx` is not found, the status is `skipped` and the load case still validates. Point `NCAD_CCX` at a
`ccx` binary to enable the solve. See the [part-to-FEA workflow](../workflows/part-to-fea.md).
