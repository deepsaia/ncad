A **relational orientation** edit reorients a face or body so it satisfies a geometric relation to
another entity, make this face parallel to that one, perpendicular to an axis, or at a set angle,
solving the required rigid transform directly rather than replaying a feature history.

## A one-shot solve

Where a parametric model would re-run a sketch and features, a relational edit computes the single
rotation (and translation) that puts the moving entity into the requested relationship, then applies
it in place. "Make face A parallel to face B" resolves to the rotation aligning A's normal with B's;
"set this face 15 degrees to that plane" resolves to the corresponding tilt.

The transform acts on **points** (the moving geometry is rigidly repositioned); construction lines
and axes are rebuilt from the moved points so the relation holds exactly. Relational edits are how
synchronous modeling captures intent on history-free geometry: instead of "these faces happen to be
parallel", the edit asserts "these faces *are* parallel" and moves the model to make it so. Like all
direct edits it targets baked geometry and references entities persistently.
