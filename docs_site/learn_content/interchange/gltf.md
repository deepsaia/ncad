**glTF** (GL Transmission Format) is the standard for delivering 3D models to real-time viewers,
the web, and game/AR engines. It is a compact, GPU-ready format: meshes, materials (physically-based
rendering), scene graph, and animations in a JSON structure with binary buffers (`.gltf` + `.bin`,
or a single packed `.glb`).

## Why glTF for the viewer

glTF is designed for *display*, not authoring: its meshes are already triangulated and its materials
map straight onto a PBR shader, so a browser can load and render it with almost no processing. This
makes it the natural output of a CAD engine's viewer path, tessellate the exact solid to a
deflection, attach per-body materials/colors, and write glTF that any WebGL viewer (or the
`<model-viewer>` web component) renders directly.

## Exact stays exact, display is glTF

glTF sits on the *approximate* side of the exact/mesh divide: it is a projection of the B-rep for
viewing, carrying no analytic geometry. Authored per-body appearance (a base-color) is written into
the glTF material so colors port to any renderer, not just one viewer. The engine keeps the B-rep as
truth and exports glTF only at the display boundary, the same discipline as STL/OBJ, but tuned for
interactive rendering rather than printing. It is why a part built from a text document can be
inspected in a browser in seconds.
