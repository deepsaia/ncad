# Workflow: import, edit, export

Bring in a dumb solid (a STEP or IGES file with no feature history), edit it directly on the B-rep,
and export it back. This is the history-free / synchronous-modeling lane: there is no feature tree to
replay, so edits act on the current geometry, guarded by a robustness oracle.

## 1. Import

`ncad import` wraps a STEP/IGES solid as an editable base-feature document (a part whose first
feature is the imported body):

```bash
ncad import path/to/model.step --out out
```

The result is an ncad part you can add features to or edit directly.

## 2. Edit directly

Direct edits act on faces of the current solid, identified by selectors, with no history to rebuild.
The shipped `examples/05-direct-modeling/` parts show the core moves:

- **`offset`** grows or shrinks the solid by a wall (`offset_shell.hocon`).
- **`defeature`** removes a detail (a boss, a hole) and heals the surface (`defeatured_block.hocon`).
- **`relate`** applies a one-shot planar relation between faces (`coaxial_bosses.hocon`).
- plus `move_face` and `reposition_hole` for nudging a face or relocating a hole on an imported solid.

```properties
{ id = thin, op = offset, distance = -2 }        # hollow the solid to a 2 mm wall
{ id = clean, op = defeature, faces = "select faces where ..." }
```

Each direct edit runs behind a three-tier validity oracle in a guarded child process, so an edit that
would hang or crash OCCT fails cleanly and is reported, rather than taking down the build.

## 3. Export

Build the edited part to any supported format:

```bash
ncad build my_edited_part.hocon --format step   # or iges, stl, 3mf, obj, ply, glb
```

`ncad build --format <fmt>` writes the chosen format(s) into `out/parts/<name>/`. STEP round-trips
exact B-rep geometry; the mesh formats (stl/3mf/obj/ply/glb) tessellate. See the
[parts guide](../guides/authoring-parts.md) for the direct-edit ops in context and the
[CLI reference](../reference/cli.md) for `import` and `build` flags.
