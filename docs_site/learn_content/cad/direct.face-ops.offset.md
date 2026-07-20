**Offset face** is a direct edit that moves a face along its own normal by a distance, thickening or
thinning the solid locally, without a feature history. Offsetting a top face outward raises a boss;
offsetting a wall inward reduces thickness. It is the history-free counterpart of editing an
extrude's depth.

## Outward is safe, inward is risky

Offsetting a face **outward** grows material and is the most robust direct operation, the kernel
extends the neighbouring faces and rarely fails. Offsetting **inward** removes material and can
exceed the local wall thickness: past the smallest wall or concave radius the offset
self-intersects and the result is invalid.

A robust modeler therefore guards inward offsets: it refuses when the distance meets or exceeds the
minimum wall thickness, and fails safe when the thickness cannot be determined. As with all direct
edits, offset acts on the current baked solid, is placed after the geometry it modifies, and
references the face persistently so it survives a rebuild. It sits within the measured direct-editing
envelope, trustworthy on simple planar geometry, fragile on complex or thin-walled solids.
