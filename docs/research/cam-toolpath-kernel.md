# Research: CAM toolpath kernel: build vs. reuse

*Question:* what toolpath engine should the CAM process profile build on, and where
is the plugin/kernel boundary? *Decision recorded in* `design.md` §6a, §19; plan
Phase 15.

## Key findings (with licenses / maintenance)

**opencamlib (OCL)**, github.com/aewallin/opencamlib
- Fundamentally a **3D surface cutter-location library**: drop-cutter (axial
  projection onto a triangulated model), push-cutter >> **waterline** constant-Z,
  cutter shapes cyl/ball/bull/cone/composite.
- Does **NOT** do 2.5D pocketing, contour offsetting, drilling cycles,
  path-linking, feeds/speeds, or posts. Adaptive/rest-milling unimplemented;
  waterline "requires a rewrite."
- **LGPL-2.1**; Boost.Python bindings; `pip install opencamlib`; latest release
  2023.1.11 (Jan 2023), low cadence but usable. `libactp` unverifiable: treat dead.

**FreeCAD Path/CAM workbench** (renamed Path>>CAM, shipped 1.0, Nov 2024)
- **2.5D area/pocket/contour** via bundled **libarea (Dan Heeks)**, which bundles
  **Clipper**. **3D surfacing/waterline** via **opencamlib**, imported optionally.
  Confirms the industry split: **Clipper for 2.5D, opencamlib for 3D.**
- **Reusability low:** op layer hard-imports `FreeCAD`/`Part`/`Path`; not importable
  without the FreeCAD runtime. Reusable pieces are the standalone C++ kernels
  (libarea/`pyarea`, opencamlib/`ocl`), not FreeCAD Python.
- Posts: modular Python-per-controller (`linuxcnc_post`, `grbl_post`,
  `generic_post`…), but **FreeCAD-coupled**. libarea BSD-3; Clipper BSL-1.0.

**Clipper2**, github.com/AngusJohnson/Clipper2 (**BSL-1.0**, actively maintained)
- Polygon boolean + **offsetting/inflation**: the core hard part of 2.5D. Python:
  **`pyclipr`** (pybind11, Clipper2, BSL-1.0) or `pyclipper` (Cython, Clipper1).

**OCCT primitives:** `BRepAlgoAPI_Section` slices a solid at a plane (loose edges >>
reassemble wires); `BRepOffsetAPI_MakeOffset` does 2D wire offset with **no
robustness guarantees**. Practical split: **OCCT for slicing, Clipper for offsets.**

**Posts:** a generic 3-axis post is a **small custom job** (G0/G1/G2/G3, F/S,
M3/M5, M7-9, M6, G20/21, G90/91, G81/G83; LinuxCNC RS274/NGC). No turnkey pip post
framework (`mecode`/`pygcode` are thin).

**The cliff:** 3-axis freeform surfacing needs a CL-point engine (opencamlib);
**5-axis (3+2 and simultaneous)** has **no credible OSS kernel** >> commercial/plugin.

## Recommendation (adopted)

- **Build 2.5D + drilling in-house** on **OCCT sections + Clipper2/`pyclipr`**. Own
  strategy logic (contour = single tool-radius offset; pocket = concentric inward
  offsets / zig-zag; facing; drill = G81/G83 at hole XY). **Skip libarea.**
- Behind the op-registry seam put **`pyclipr` (Clipper2, BSL-1.0)** as the
  offsetting kernel: permissive, maintained, no GPL entanglement. Do **not** put
  FreeCAD behind the seam (runtime-coupled).
- **Write a small generic 3-axis post** (FreeCAD's per-controller scripts are the
  design template, not a dependency); keep posts pluggable.
- **Plugin/kernel boundary at 3D surfacing:** expose **opencamlib (LGPL-2.1)** as an
  optional plugin for drop-cutter/waterline finishing. **5-axis out of scope**,
  reserve for a future external-kernel plugin.

**Confidence:** high on the split + licenses (repos/PyPI/OCCT docs, corroborated by
FreeCAD's architecture). **Biggest unknown:** engineering cost/robustness of a
*good* pocketing strategy on raw Clipper2 (corners, thin-wall/rest, lead-in/out).
The offset primitive is solid; the strategy layer concentrates the risk.
