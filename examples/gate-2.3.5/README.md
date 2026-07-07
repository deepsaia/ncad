# gate-2.3.5: spline / curve sketch entities

- `spline_profile.hocon` - a closed profile whose top edge is an `interpolated` spline,
  extruded to a solid. Proves closed-loop spline >> face >> solid.
- `bezier_sweep.hocon` - a small circular profile swept along an open `bezier` path.
  Proves smooth sweep paths from spline entities.

Both are slow STEP round-trips (see `tests/build/test_splines.py`).
