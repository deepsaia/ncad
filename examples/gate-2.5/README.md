# gate-2.5: rib / web / stiffener

- `t_rib.hocon` - a straight rib on a base plate: an open XZ profile thickened and grown
  into the plate, unioned.
- `curved_rib.hocon` - the same base with an arc rib profile (proves `trace` on curved
  wires).

Both are slow STEP round-trips (see `tests/build/test_rib.py`).
