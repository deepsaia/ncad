# Gate 2.3: Sweep + helical sweep / coil

One `sweep` op, fed by a sketch open-mode wire path or a generated helix.

- `swept_pipe.hocon` , a circular profile swept along a rounded-corner path (a sharp
  corner drops the leg; the arc sweeps the whole length). Single-path sweep.
- `coil_spring.hocon` , a circular profile swept along a generated helix (coil).
- `hvac_duct.hocon` , a large 120x80 rectangular duct swept along a run with a rounded
  90-degree elbow (rise + elbow + horizontal run), like a real HVAC duct. The elbow radius
  exceeds half the profile width so the inside of the bend does not self-intersect.

A sketch with `open = true` emits an open wire (a path) instead of a face. Paths are
line + arc + helix; smooth spline paths come with the next (spline entity) bucket, and
sweep picks them up for free. `anchor` (origin/centroid/[x,y]) places the profile on the
path start; `is_frenet`/`transition` control orientation and corners.

Gate (2.3): a swept pipe, a coil, and an HVAC duct build and export clean STEP.
