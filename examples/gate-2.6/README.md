# gate-2.6: chamfer variants

- `two_distance_chamfer.hocon` - an asymmetric (distance + distance2) chamfer on the
  vertical edges of a block.
- `angle_chamfer.hocon` - a distance-angle chamfer (raw-OCP per-edge AddDA) on the vertical
  edges.

Both are slow STEP round-trips (see `tests/build/test_chamfer_variants.py`).
