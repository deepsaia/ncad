# Python API reference

Everything the CLI does is available as importable classes. Imports are always from the concrete
module that defines a symbol (the package `__init__.py` files are empty by policy), for example
`from ncad.build.document_builder import DocumentBuilder`. The builder classes take a geometry
`kernel`, normally `ncad.kernel.build123d_kernel.Build123dKernel`.

## Build

`ncad.build.document_builder.DocumentBuilder(kernel)`

- `.build(document: dict) -> dict[str, OpResult]` - strict; raises on an invalid design.
- `.build_file(path, out_dir, formats=("glb",), layout_kind="parts", mesh_tolerance=None) -> dict` -
  agent-facing; reports bad design as diagnostics data, never raises. Returns
  `{"artifacts": {part: path}, "diagnostics": [...]}`.
- `.build_file_document(path) -> dict[str, OpResult]`.

Module helper `resolve_formats(formats) -> tuple` validates against
`glb, step, iges, stl, 3mf, obj, ply`.

## Assembly and motion

- `ncad.assembly.assembly_builder.AssemblyBuilder(kernel).assemble(asm_path, out_dir,
  motion_spec=None) -> dict` - composes an assembly to a scene sidecar.
- `ncad.assembly.motion_builder.MotionBuilder(kernel).build(motion_path, out_dir) -> dict` - solves a
  motion study to a trajectory sidecar.

## Robotics

- `ncad.robotics.robot_model_builder.RobotModelBuilder(kernel).build(physics_path, out_dir) ->
  (RobotModel, warnings)` - derives the neutral `RobotModel` (links + joints + computed inertials +
  per-link meshes).
- `ncad.robotics.robot_model.RobotModel` - `.tree_joints()`, `.loop_closures()`.
- `ncad.robotics.robot_format.robot_writer(export_format) -> (writer, extension)` - dispatch for
  `urdf` / `mjcf` (`.xml`) / `sdf`. The writers (`UrdfWriter`, `MjcfWriter`, `SdfWriter`) each expose
  `.to_xml(model) -> str`.
- `ncad.robotics.robot_sidecar_builder.RobotSidecarBuilder(kernel).build(physics_path, out_dir,
  with_sweeps=True) -> dict` - writes the viewer `.robot.json` (+ optional sweeps).
- `ncad.robotics.robot_collision_checker.RobotCollisionChecker(kernel).check(physics_path, tree, pose)
  -> list[dict]` - self-collision at a pose.

## FEA

`ncad.fea.analysis_document.AnalysisDocument().run(analysis_path, out_dir) -> dict` - mesh + delegate
solve + read results. Returns `{status, artifact, sidecars, summary, mesh, warnings}` where `status`
is `generated | skipped | failed`; never raises for a missing gmsh/ccx.

## Standard parts

`ncad.standard.standard_library.StandardLibrary()` - `.families()`, `.subtypes(family)`,
`.designations(family, subtype=None)`, `.required_dimensions(family, subtype=None)`,
`.generate(family, designation, ...) -> dict`, `.generate_custom(family, dimensions, ...) -> dict`,
`.provenance(family, subtype=None)`.

## Viewer, rendering, export

- `ncad.viewer.snapshot_renderer.SnapshotRenderer(width=800, height=600, frames=24).render(
  model_path, out_dir=None) -> {"png", "gif"}` - offscreen still + orbit GIF.
- `ncad.viewer.model_exporter.ModelExporter(kernel).export(source, kind, fmt, base_name, part) ->
  (download_name, content_type, bytes)`.
- `ncad.viewer.viewer_server.ViewerServer(models_dir, host, port, ...)` and
  `ncad.service.ncad_service.NcadService(models_dir, host, port, ...)` - the two servers;
  `.serve_forever()`, `.start()`, `.stop()`.

## The CLI facade

`ncad.cli.viewer_cli.ViewerCli` is itself a usable programmatic facade: every CLI action is a method
(`build_document`, `import_document`, `assemble_document`, `motion_document`, `physics_document`,
`analyze_document`, `validate_document`, `snapshot_model`, `dfm_document`, `standard_part`,
`slice_model`), each importing the kernel lazily.
