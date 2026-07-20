A **sketch** is a set of 2D geometric entities drawn on a plane, the profile that solid features
extrude, revolve, or sweep. The two most primitive entities are the **point** and the **line
segment**.

A **point** is a single location $(x, y)$ in the sketch plane. Points serve as explicit vertices,
as endpoints that other entities share, and as references (a hole centre, a pattern seed). A
**line segment** connects two points and is the straight edge of most profiles.

<figure markdown="span">
<svg viewBox="0 0 320 160" width="360" role="img" aria-label="Two line segments sharing a corner point" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="40" y1="120" x2="220" y2="120"/>
  <line x1="220" y1="120" x2="220" y2="30"/>
  <circle cx="40" cy="120" r="4" fill="currentColor"/>
  <circle cx="220" cy="120" r="5" fill="currentColor"/>
  <circle cx="220" cy="30" r="4" fill="currentColor"/>
  <text x="30" y="140" fill="currentColor" stroke="none" font-size="13">p1</text>
  <text x="228" y="140" fill="currentColor" stroke="none" font-size="13">p2 (shared)</text>
  <text x="228" y="28" fill="currentColor" stroke="none" font-size="13">p3</text>
</svg>
<figcaption>Two segments meeting at a shared endpoint p2: the corner stays closed under edits.</figcaption>
</figure>

## Why entities are more than coordinates

In a parametric sketch, an entity is not a fixed pair of numbers, it is a variable whose position
the constraint solver determines. A line's endpoints are unknowns; constraints (a length
dimension, a horizontal relation, a coincidence with another entity) pin them down. This is what
lets a sketch be *edited*: change a driving dimension and the solver recomputes every dependent
entity, rather than the author moving each vertex by hand.

Endpoints are shared, not duplicated: when two segments meet at a corner, they reference the *same*
point entity, so a coincidence is implicit and the corner stays closed under edits. A profile that
a feature can use must form a closed loop of such connected entities.
