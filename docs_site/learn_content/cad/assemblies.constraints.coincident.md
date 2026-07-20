A **coincident mate** forces two entities of different parts to share a location or lie on a common
element: two faces flush (**coincident/flush**), two axes collinear (**concentric**), a point on a
plane. It is the 3D-assembly counterpart of the sketch coincidence constraint.

## The mate vocabulary

Assembly constraints are a small, closed set of user-facing mates, coincident, flush, concentric,
parallel, perpendicular, angle, distance, lock, that read as design intent. Coincident/concentric
are the most common: they seat a shaft in a bore (concentric axes), sit a part flat on a table
(coincident faces), or center a pin in a hole.

## Lowering to primitives

Each user mate **lowers** to a small set of primitive constraints on connector frames (align these
origins, make these axes collinear, keep these planes coincident). The primitive core is what the
solver actually consumes; the friendly mate vocabulary is sugar over it, the same pattern as
sketch-entity sugar over primitive geometry. A mate removes degrees of freedom from the assembly's
joint graph, and the constraint solver finds the placement that satisfies all mates simultaneously,
exactly the sketch solver, one dimension up.
