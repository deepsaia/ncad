**Construction geometry** is sketch entities that shape and constrain the profile but are *not*
part of it, they never become an edge of the resulting solid. A line or circle is flagged as
construction (also called reference) geometry, drawn in a distinct style, and ignored when the
sketcher extracts the closed profile a feature uses.

Common uses:

- A **centreline** for a symmetry constraint or a revolve axis.
- A **construction circle** carrying a bolt-circle of holes (the circle positions the points; only
  the holes are real).
- A diagonal **reference line** whose length or angle a driven dimension measures.
- A pitch line a slot or rib is built about.

## Why it is separate from the profile

Construction geometry lets the author express intent, symmetry axes, bolt circles, alignment
lines, without polluting the profile. If a construction circle were a real entity, the feature would
try to extrude it. Marking it construction keeps the profile clean while still contributing
constraints and reference frames. It is the sketch-level counterpart of 3D datums: geometry that
exists to *locate and relate* other geometry, not to become material.
