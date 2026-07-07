# gate-2.4: loft

- `lofted_transition.hocon` - a square base blended smoothly to a circle 40 above it
  (square-to-round transition). Multi-plane sections via `plane_offset`.
- `lofted_cone.hocon` - a circular base lofted to an apex point (`end_point` vertex cap).
- `ruled_loft.hocon` - two square sections with `ruled = true` (straight-blend facets).

All are slow STEP round-trips (see `tests/build/test_loft.py`).
