# Gate 1.4: reference-into-sketch (+ offset)

Proves reference-into-sketch: a sketch can project a prior feature's edges onto its plane
as fixed reference (construction) geometry, and offset them (or any entity) into a real
profile. Projected geometry is pinned to its source and excluded from the built wire;
generated ids are zero-padded so they sort correctly.

```bash
ncad build examples/gate-1.4/projected_ring.hocon
ncad build examples/gate-1.4/projected_inset.hocon
ncad
```

- `projected_ring.hocon`: a disc, then a sketch that projects the disc's top circular
  edge and offsets it inward to make a concentric ring (washer), extruded taller. The gate
  case: project a prior face edge and offset it into a profile that builds.
- `projected_inset.hocon`: a cylindrical post, then a sketch projecting the post's bottom
  circular edge offset outward into a wider base flange. Shows offsetting a projected
  curve the other way (outset).

Sketch-modify (trim, extend, mirror, pattern, and whole-loop offset with corner handling)
is bucket 1.4b.
