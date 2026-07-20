**Orientation constraints** fix the direction of entities relative to the sketch axes or to each
other: **horizontal**, **vertical**, **parallel**, and **perpendicular**.

- **Horizontal** / **vertical** align a line with the sketch's X or Y axis, each removing one
  rotational degree of freedom.
- **Parallel** forces two lines to share a direction; **perpendicular** forces their directions
  $90^\circ$ apart.

<figure markdown="span">
<svg viewBox="0 0 320 130" width="340" role="img" aria-label="Perpendicular and parallel lines" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="30" y1="100" x2="130" y2="100"/>
  <line x1="30" y1="100" x2="30" y2="30"/>
  <path d="M 30 82 L 48 82 L 48 100" stroke-width="1.5"/>
  <text x="55" y="40" fill="currentColor" stroke="none" font-size="12">perpendicular</text>
  <line x1="200" y1="40" x2="300" y2="55"/>
  <line x1="200" y1="90" x2="300" y2="105"/>
  <text x="205" y="125" fill="currentColor" stroke="none" font-size="12">parallel</text>
</svg>
<figcaption>A perpendicular corner (left) and a parallel pair (right), each a directional relation.</figcaption>
</figure>

## Why direction constraints matter

Orientation constraints capture design intent that must survive edits: a bracket's back face is
*vertical* because it is constrained vertical, not because its endpoints currently happen to have
equal X. When a driving dimension changes and the solver moves geometry, orientation constraints
keep walls square and edges aligned. They pair naturally with dimensional constraints: orientation
fixes *direction*, dimensions fix *size*, and together they drive a fully-defined sketch.
