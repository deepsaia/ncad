**Delete face** (defeature) removes a feature from a solid by deleting its faces and healing the
gap, without editing a feature history. Select the faces of an unwanted boss, fillet, or hole and
the kernel removes them and extends the surrounding surfaces to close the wound. It is the primary
tool for simplifying imported or dumb geometry: strip a chamfer, remove a logo, delete a small hole.

## Healing and its limits

After removing the faces, the kernel must **heal** the boundary, extend and re-intersect the
neighbouring faces to reform a closed solid. This works cleanly when the removed feature sits on
simple planar or analytic faces of a single body. It fails when the neighbours are non-planar, when
the removed face is tangent-adjacent to a fillet (the heal is ill-defined), or on sliver/small
faces.

A robust modeler guards defeature accordingly: it refuses a multibody target, a non-planar target
face, a sliver, or a tangent-adjacent face, and fails safe when a needed fact is unavailable, so a
fragile heal is never attempted. Defeature is the highest-value direct edit for cleaning up
interchange geometry, but also among the most fragile, which is why the safe envelope is enforced
before the kernel runs.
