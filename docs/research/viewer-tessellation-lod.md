# Viewer tessellation, LOD, and the renderer question

Two viewer problems and their honest fixes: (1) complex parts (a coil, a spring, a threaded
hole) explode into a huge triangle mesh that renders slowly, while coarsening the mesh makes
curved surfaces look faceted; and (2) the viewer's displayed axes must match the *modeled*
frame (a face authored facing +Z should read +Z in the viewport). This note records the
analysis, rejects two tempting-but-wrong solutions (retopology, switching web renderer), and
lays out the staged fix. It backs the plan's viewer-upgrade bucket (2.8a).

## The framing correction that drives everything

ncad's meshes are **not the source of truth**, the exact B-rep is (design §0). Triangles
are a *disposable approximation* generated at export time for display. So this is a
**tessellation-budget / level-of-detail (LOD)** problem, not a mesh-topology problem. Two
consequences:

- **Retopology is the wrong tool.** Remeshing to a clean quad/tri layout is for editing
  *authored* meshes (animation/deformation). It moves vertices off the exact surface
  (uncontrolled geometric error), is expensive, and its output is not a stable function of
  the spec, so it would fight §4a determinism. We do not retopologize.
- **Blender is the wrong reference.** Blender is mesh-native: its polygon count *is* the
  authored artifact, so it never has our "approximate an exact surface at a viewing budget"
  problem. Its subsurf/remesh/decimate tools edit authored topology; they do not tessellate
  analytic surfaces on demand. The right reference is how **CAD** viewers (Onshape, Fusion,
  FreeCAD) tessellate B-rep, which is the adaptive-deflection / LOD path below, and which
  OCCT already provides. (The one Blender *interaction* idea worth borrowing is in the plan:
  coarse-while-moving, refine-on-idle.)

## Issue 1: adaptive tessellation, not retopology

**Current state** (`build123d_kernel.py`): a fixed `linear_deflection = 0.2% of bbox
diagonal` plus `angular_deflection = 0.2 rad`. On a coil/thread, geometry is all
high-curvature surface with a large surface-to-bbox ratio, so the angular term dominates and
the triangle count explodes. Coarsening uniformly then facets the silhouette (the "weird
low-poly faces").

Key insight: **perceived smoothness on a curved surface comes mostly from per-vertex
normals**, which ncad already exports and smooth-shades (the `flatShading: false` viewer
material). So the mesh can be *coarser than it looks* if normals are good; faceting appears
when the **silhouette** is under-tessellated, not the interior.

**The fix, staged:**

1. **Adaptive deflection to a triangle budget (do first, export-side).** Instead of a fixed
   0.2% deflection, tessellate and, if the triangle count exceeds a budget (start ~200k-500k
   tris/part, tune against real coil/thread examples), increase deflection and re-tessellate
   until under budget. A coil then auto-coarsens to an adequate mesh; a flat bracket stays
   crisp. This is the "simplified reps / LOD" the design already anticipates (§7, §13).
   Deterministic (a pure function of spec + budget), so it stays golden-testable per §4a,
   the budget just becomes part of the pinned tessellation parameters.
2. **glTF mesh compression.** Ship `EXT_meshopt_compression` (via `meshoptimizer`) or
   `KHR_draco_mesh_compression` on the exported glb. Cuts transfer/parse cost for heavy
   meshes with loaders three.js already supports.
3. **Interaction LOD (the Blender trick, cheap).** Hold a coarse mesh during camera
   orbit/pan and swap to the fine mesh on idle, so heavy models *feel* fast regardless of
   count. A viewer-side behavior on top of (1).
4. **Optional: decimation post-step.** If (1) is not enough, tessellate exact then run
   quadric edge-collapse decimation (`meshoptimizer` / `trimesh`) to the budget, this is the
   *legitimate* cousin of retopology: fast, error-bounded, surface-preserving. Prefer (1)
   because it never generates the excess triangles in the first place.

Expose the budget as a viewer setting (draft / normal / fine).

## Issue 2: displayed axes must equal modeled axes

**This is a real coordinate-frame bug, not just labels.** Today (`viewer_page.html`, the
orientation-gizmo block): models are authored **Z-up** (§0), but `export_gltf` lands them
**Y-up** in the three.js scene (glTF is Y-up, an effective -90 deg about X: part +Z ->
viewport +Y, part +Y -> viewport -Z). The viewer does **not** rotate the geometry back; it
leaves the mesh Y-up and only feeds the *orientation gizmo* a proxy camera rotated by the
inverse so the gizmo *labels* read Z-up.

So the gizmo is relabeled to look Z-up while the geometry sits Y-up. It is self-consistent
if you only read the gizmo, but the moment anything uses true scene space (measurement, a
section plane, a datum readout, a "top" view), **+Z is not where the gizmo claims it is.**
That mismatch is the bug.

**The fix: make scene coordinates equal modeled coordinates, then axes are correct by
construction (and the gizmo proxy-camera trick disappears).** Either:

- **Viewer-side (simplest):** wrap the loaded glTF in a group rotated +90 deg about X
  (undoing the glTF Y-up landing) and set `camera.up = (0, 0, 1)`. Scene space then *is*
  part space; a +Z face points +Z; the gizmo labels world axes directly with no proxy.
- **Export-side:** tell the glTF writer the model is Z-up so no rotation is baked in, then
  the viewer only sets `camera.up = Z`. Cleaner (no per-load rotation) but depends on the
  exporter honoring the up-axis.

Either way, delete the gizmo's inverse-rotation compensation; it is a workaround that will
keep biting every feature that reads real coordinates (measurement, sectioning, PMI).

## The renderer question: keep three.js

Switching web renderers treats a *data* problem as a *renderer* problem. The coil is slow
because it is too many triangles; no renderer makes millions of pointless triangles fast, so
Babylon.js / PlayCanvas / raw WebGPU would choke on the same bad mesh. **The bottleneck is
upstream of three.js.** three.js also already has `LOD`, a maturing WebGPU backend (still
needs a WebGL fallback), and Draco/meshopt loaders. Switching is a large cost for zero gain
on the actual problem. **Do not switch.**

## Out-of-the-box options considered (and where they land)

- **Client-side tessellation via OpenCASCADE.js (WASM), the real ceiling-raiser.** Ship the
  exact B-rep to the browser and tessellate *view-dependently* (coarse zoomed out, fine
  zoomed in, always off the exact surface), plus exact client-side measurement/sectioning.
  Confirmed real and used in 2024-25 (ocjs.org, multiple STEP viewers). This is **already in
  the design as a deferred item (§13)**, not a detour. The unmeasured cost is the multi-MB
  WASM kernel download; measure before committing. Target: a later phase (§13/Phase 14), not
  bucket 2.8a.
- **Nanite-style meshlet cluster-LOD on WebGPU** (`Scthe/nanite-webgpu`, `zeux/meshoptimizer`
  experimental cluster-LOD). Renders millions of triangles via GPU-driven culling. Real but
  a single-dev research effort, Chrome-only WebGPU, experimental. Overkill for a part viewer;
  only interesting at massive-assembly scale (§7/§12), and even there the staged fix above
  likely suffices. **Watch, do not build.**

## Recommendation

For bucket 2.8a, do the deterministic export-side + viewer-side work: **(1) adaptive
deflection to a triangle budget, (2) glTF mesh compression, (3) interaction LOD
(coarse-while-moving), and the (Issue 2) Z-up scene fix.** Keep three.js. Leave client-side
WASM tessellation and Nanite-web to their proper later phases.

**Confidence:** high on the framing (tessellation-budget not retopology; renderer is the
wrong layer; the axis issue is a real Z-up/Y-up frame bug) and on OpenCASCADE.js /
nanite-webgpu existing; **medium** on the specific triangle-budget numbers (tune against real
examples) and **unmeasured** on the WASM-kernel download cost, which is the thing to measure
before committing to client-side tessellation. **Biggest open question:** how much of ncad's
real geometry actually blows the budget (is this a coil/thread edge case or a broad problem?),
which decides whether adaptive deflection alone is the whole fix or just step one.
