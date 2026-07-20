**Syntactic sugar** entities are convenience shapes that expand into the primitive entities
(points, lines, arcs) plus their constraints. A **rectangle**, a **regular polygon**, and a
**slot** are the common ones: an author draws one high-level shape and the sketcher emits the
underlying segments already constrained.

- A **rectangle** expands to four line segments with two horizontal and two vertical relations
  (and often equal-length pairs), so it stays rectangular under edits, changing the width dimension
  moves both vertical sides.
- A **regular polygon** expands to $n$ equal segments on a construction circle with equal-angle
  spacing, parameterized by the number of sides and a circumradius or across-flats dimension (a hex
  for a bolt head).
- A **slot** expands to two parallel lines capped by two tangent semicircle arcs, driven by a
  length and a width.

## Why sugar matters

Sugar entities encode *design intent* directly: a rectangle is not four independent lines that
happen to form a box, it is a shape that *remains* a box because its constraints say so. This keeps
sketches robust under parametric edits and dramatically reduces the number of constraints an author
places by hand. Under the surface it is still primitives and constraints, so the solver and every
downstream feature treat it uniformly.
