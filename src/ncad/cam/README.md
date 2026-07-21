# CAM: slicing to G-code

`ncad slice <model.stl> --profile <wrapper.json>` slices an STL to G-code by DELEGATING to a slicer
the user has installed. ncad owns the model, the mesh export, and the verified handoff; the slicing
algorithm and its settings stay in the slicer.

## The boundary (what ncad does / does not own)

| ncad owns | delegated to the slicer |
|-----------|-------------------------|
| the B-rep model + computed mass properties | the slicing algorithm |
| the STL/3MF export a slicer consumes (Stage 0) | layer height, temps, supports, infill (its config) |
| locating the slicer, invoking it, validating the G-code, recording the artifact + report | the G-code generation itself |

ncad **does not bundle a slicer** and **does not require one**: with no slicer installed, `ncad
slice` reports `skipped` (never a silent pass) and the rest of ncad is unaffected. It **stops at
G-code** - printer/LAN control is out of scope. This is the same delegation pattern as the robotics
export (ncad emits URDF/MJCF; the user runs MuJoCo/ROS).

## Slicers

No open-source slicer ships as a pip package, so ncad delegates to an installed binary, found by
preference order via `shutil.which`:

- **OrcaSlicer**, **PrusaSlicer**, **Slic3r** share the CLI form
  `--load <config> --export-gcode --output <out> <stl>`.
- **CuraEngine** uses `slice -j <config> -l <stl> -o <out>`.

Because ncad only shells out to a separately-installed binary (never links or vendors it), the
slicers' AGPL/GPL licensing does not affect ncad's license.

## Profile wrapper

ncad does not own slicer settings; a slice profile is a thin wrapper pointing at the slicer's OWN
config file plus a slicer preference:

```json
{ "config": "petg_0.2mm.ini",
  "slicers": ["orca", "prusa"],
  "extra_args": ["--support-material"] }
```

`config` is resolved relative to the wrapper. `slicers` is the preference order (default: all known,
best first). `extra_args` pass through to the slicer verbatim.

## Report

The run returns a delegation report: `status` = `generated` | `skipped` | `failed`, plus the slicer
used, the artifact path, the checks that ran, the skip/failure reasons, and G-code stats (layers,
motion commands, extrusion present). `GcodeValidator` confirms the output is real toolpath G-code
(motion commands with axis words) rather than trusting the slicer's exit code.
