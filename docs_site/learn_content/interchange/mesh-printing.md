**STL**, **3MF**, and **OBJ** are triangle-mesh formats, the lingua franca of 3D printing and
mesh pipelines. Unlike STEP (exact B-rep), these carry a **tessellated approximation** of the
surface: a net of triangles at a chosen deflection.

- **STL** is the oldest and simplest: a bare list of triangles (facets + normals), no units, no
  color, no structure. Universally supported by slicers, and the reason "export STL" is synonymous
  with "send to print".
- **3MF** is the modern replacement: an XML/ZIP container that fixes STL's gaps, units, color,
  materials, multiple objects, and print metadata, in one well-defined package.
- **OBJ** is the graphics-world mesh format: geometry plus optional texture coordinates and material
  references, common in rendering and asset pipelines.

## Where they fit

A modeling engine produces these by **tessellating** the exact solid to the required deflection,
finer for a show surface, coarser for a quick check. They are a one-way, lossy projection: you print
or render from them, you do not machine or re-feature from them (that needs the B-rep via STEP).
Choosing the format follows the destination: STL or 3MF for a printer (3MF when color/units/multi-
part matter), OBJ for a renderer. Deterministic tessellation keeps the exported mesh reproducible.
