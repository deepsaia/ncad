# Gate 1.2: the full sketch entity vocabulary

Proves the entity vocabulary beyond lines: first-class arcs and circles, plus the
polyline / slot / regular-polygon sugar that lowers to primitives. A profile mixing
straight and curved edges is solved and built into a face via the kernel's mixed-edge
wire builder (`wire_face`).

```bash
ncad build examples/gate-1.2/rounded_bar.hocon
ncad build examples/gate-1.2/slotted_tab.hocon
ncad
```

- `rounded_bar.hocon`: a D-shaped profile (3 lines + 1 arc cap), the mixed straight and
  curved profile proof. The arc center is left free (an under-constrained warning) until
  symmetry/midpoint constraints arrive in bucket 1.3.
- `slotted_tab.hocon`: one body from two curved sketches, a slot-shaped plate (the slot
  sugar, 2 lines + 2 semicircular arc caps, solving to an exact stadium) with a round
  hole pocketed through it (a first-class circle dimensioned by a radius constraint).
