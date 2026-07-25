# Workflow: part to FEA

Take a part into a structural finite-element load case and read the results. ncad owns the model and
delegates the solve to CalculiX (`ccx`), which is not bundled; without it the run degrades to a
`skipped` status and the load case still validates.

## 1. The part

`examples/10-fea/bracket.hocon` is an ordinary feature-tree part (an L-bracket). Build it to confirm
the geometry before analyzing:

```bash
ncad build examples/10-fea/bracket.hocon && ncad view
```

## 2. The load case

`bracket.analysis.hocon` is an overlay on that part: a mesh spec, boundary conditions, loads, and the
analysis steps. Here a fixed base, a tip pressure plus gravity, and three steps (static stress, first
modes, steady thermal):

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

## 3. Run and read

```bash
uv sync --extra fea      # gmsh + meshio (mesh + result IO; the ccx solver is separate)
ncad analyze examples/10-fea/bracket.analysis.hocon
ncad view                # Analyze mode: the field mesh, colored by von Mises
```

ncad meshes the part (Gmsh, into quadratic tets), composes the CalculiX deck, delegates the solve,
and reads the `.frd` results into `out/analyses/bracket/bracket.analysis.json`: peak von Mises,
displacement magnitude, and the eigenfrequencies. Units are SI throughout (the deck is in metres,
stress in Pa). Point `NCAD_CCX` at a `ccx` binary to enable the solve; without it the status is
`skipped`.

## Notes

- Faces are selected by keyword (`top`, `bottom`, `all`, `vertical`, `horizontal`), so the load case
  survives a part rebuild.
- More cases ship under `examples/10-fea/` (a con-rod, an F1 front wing). The
  [analyses guide](../guides/authoring-analyses.md) covers the full vocabulary.
