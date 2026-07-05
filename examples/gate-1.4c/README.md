# Gate 1.4c: Sketch-modify topology

Demonstrates the intersection-based topology ops (a `TopologyApplier` pre-solve stage):
`trim`, `extend`, `fillet` (corner), `chamfer` (corner).

- `trimmed_mirror.hocon` , a right-side open chain whose overshooting top edge is trimmed
  back to the right edge (welding to its top corner), then mirrored across the Y axis to
  close a symmetric plate. Satisfies the gate's "a sketch trimmed + mirrored builds".
- `filleted_plate.hocon` , a rectangle whose two top corners are rounded by a corner
  fillet (each trims the corner lines to their tangent points and inserts a tangent arc).

Both build a single closed face on the FakeKernel gate sweep and the real kernel.

Gate: a sketch trimmed + mirrored builds; a linear sketch pattern replicates (the pattern
half is covered by gate-1.4b).
