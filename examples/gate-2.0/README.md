# Gate 2.0: Document-level STEP export

Proves ncad exports **STEP** (exact B-rep CAD interchange), not just glb (a display mesh).
glb is how the viewer shows a model; STEP is how the exact solid leaves ncad for FreeCAD /
SolidWorks / manufacturing (design section 14). The two are different representations:
glb is lossy triangles, STEP is the real surfaces + topology + units.

- `step_block.hocon` , a sketched-and-extruded block. `ncad build step_block.hocon
  --format step` writes `step_block.step`; the gate test re-imports it as a valid solid
  with matching volume (a structural round-trip, per design section 4a).

Build both at once: `ncad build step_block.hocon --format glb,step`.

Gate (2.0): a built part exports clean STEP that re-imports as a valid solid.
