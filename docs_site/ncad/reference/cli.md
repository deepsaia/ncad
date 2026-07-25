# CLI reference

`ncad` is a single typer app and the one entry point; it runs from anywhere inside the project (it
finds the project root by walking up for `pyproject.toml`). Default directories resolve against that
root: models to `<root>/out`, examples to `<root>/examples`.

| Command | Purpose |
| --- | --- |
| `ncad` (bare) | launch the browser viewer (same as `ncad view`) |
| `ncad view` | browser 3D viewer + model manager over a models dir |
| `ncad serve` | the full Tornado HTTP service (JSON API + viewer + Swagger) |
| `ncad build` | build a feature-tree part document to glTF (+ sidecars) |
| `ncad import` | import a STEP/IGES solid as an editable base-feature part |
| `ncad assemble` | compose an assembly (placed part instances) into a scene |
| `ncad motion` | run a motion study (assembly + driver) into a trajectory |
| `ncad physics` | export a robot description (urdf/mjcf/sdf) from a physics overlay |
| `ncad analyze` | run a structural FEA load case (mesh + solve + read) |
| `ncad slice` | slice an STL to G-code via an installed slicer (delegated) |
| `ncad validate` | statically validate a document (no geometry); exit 1 if not ok |
| `ncad snapshot` | render a model to a PNG still + orbit GIF (offscreen) |
| `ncad dfm` | manufacturability preflight against a process's DFM rules |
| `ncad spgen` | generate a standard part (by designation or custom dims) |

A second console script, `ncad-build`, is equivalent to `ncad build` (with an extra
`--mesh-tolerance` flag).

## Common flags (view / serve)

- `--host TEXT` bind address (default `127.0.0.1`; `serve` falls back to `NCAD_HOST`).
- `--port INT` bind port (default `8000`; `0` picks a free port; `serve` falls back to `NCAD_PORT`).
- `--dev / --no-dev` hot-reload (default on).

## Commands

### `ncad` (bare) / `ncad view`

Launch the stdlib browser 3D viewer + model manager. Positional `models_dir` (optional, default
`out/`). Flags: `--host`, `--port`, `--dev / --no-dev`.

### `ncad serve`

Run the Tornado HTTP service: versioned JSON API under `/api/v1`, the viewer SPA at `/viewer`, Swagger
UI at `/docs`. Positional `models_dir` (optional, default `out/`). Flags `--host` / `--port` /
`--dev` default to the `NCAD_*` env values (flag > env > default). See the
[HTTP API reference](http-api.md).

### `ncad build`

Build every part in a feature-tree document to the chosen format(s).

- Positional `document` (required): a `.hocon` / `.json` part document.
- `--out TEXT` output dir (default `out/`).
- `--format, -f TEXT` comma-separated formats (default `glb`). Supported: `glb, step, iges, stl, 3mf,
  obj, ply`.

### `ncad import`

Import a dumb solid (STEP/IGES) as an editable base-feature document.

- Positional `file` (required): a STEP/IGES file. `--out TEXT` (default `out/`).

### `ncad assemble`

Compose an assembly into a viewable scene.

- Positional `document` (required): a `.asm.hocon`. `--out TEXT` (default `out/`).

### `ncad motion`

Drive a mechanism: run a motion study into a trajectory.

- Positional `document` (required): a `.motion.hocon`. `--out TEXT` (default `out/`).

### `ncad physics`

Export a robot description from an assembly + physics overlay (computed inertia).

- Positional `document` (required): a `.physics.hocon`. `--out TEXT` (default `out/`).
- `--sidecars / --no-sidecars` also write the `.robot.json` viewer tree (default on).
- `--sweeps` also solve per-actuated-joint articulation sweeps (default off).

### `ncad slice`

Slice an STL to G-code via an installed slicer (delegation; stops at G-code).

- Positional `stl` (required): an STL (from `ncad build --format stl`).
- `--profile, -p TEXT` (required): a slice-profile wrapper JSON. `--out TEXT` (default `out/`).

### `ncad analyze`

Run a structural FEA load case: mesh (gmsh) + solve (delegated CalculiX ccx) + read results.

- Positional `document` (required): a `.analysis.hocon`. `--out TEXT` (default `out/`).

### `ncad validate`

Statically validate a part / assembly / motion document (no geometry). Prints diagnostics and exits
`1` if not ok.

- Positional `document` (required): a `.hocon` / `.json` document.

### `ncad snapshot`

Render a model to a PNG still + orbit GIF review packet (offscreen, no viewer).

- Positional `model` (required): a built model (glb/stl/obj/ply/3mf).
- `--out TEXT` (default: beside the model). `--frames INT` orbit frames in the GIF (default `24`).

### `ncad dfm`

Manufacturability preflight: check each part against a process's DFM rules (tri-state
pass/fail/need-info); writes a `.dfm.json` per part.

- Positional `document` (required): a `.hocon` / `.json` document.
- `--process, -p TEXT` (repeatable, default `laser`): `laser, waterjet, cnc_sheet, fdm`.
- `--out TEXT` (default `out/`). `--rules TEXT` external DFM rule file (default: shipped limits).

### `ncad spgen`

Generate a standard part natively, persist a `.hocon`, and build it. See the
[standard parts guide](../guides/standard-parts.md).

- Positional `family` (required): e.g. `washer, hex_nut, pipe, flange, gasket, bearing, i_beam`, or
  grouped `pipe_fitting`.
- Positional `arg1` / `arg2` (optional): the designation, or a subtype + designation for a grouped
  family (e.g. `pipe_fitting elbow DN50`).
- `--dim, -d TEXT` (repeatable): custom `key=value` dimensions (mm); replaces the table lookup.
- `--out TEXT` (default `out/`).
