**Arcs** and **circles** are the curved primitives of a 2D sketch. A **circle** is the locus of
points a fixed radius $r$ from a centre point; an **arc** is a bounded portion of a circle between
two endpoints, carrying a centre, a radius, and a sweep direction.

<figure markdown="span">
<svg viewBox="0 0 320 160" width="340" role="img" aria-label="A circle and an arc" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="90" cy="80" r="45"/>
  <circle cx="90" cy="80" r="3" fill="currentColor"/>
  <line x1="90" y1="80" x2="135" y2="80" stroke-dasharray="4 3"/>
  <text x="105" y="74" fill="currentColor" stroke="none" font-size="12">r</text>
  <path d="M 210 125 A 55 55 0 0 1 265 70"/>
  <circle cx="210" cy="125" r="4" fill="currentColor"/>
  <circle cx="265" cy="70" r="4" fill="currentColor"/>
</svg>
<figcaption>A full circle (centre + radius) and a 90 degree arc bounded by two endpoints.</figcaption>
</figure>

## Why they are constrained, not just placed

Like all sketch geometry, arcs and circles are solver variables. A circle contributes its centre
$(x, y)$ and radius $r$ as unknowns; an arc adds its two endpoint angles. Constraints fix them: a
**tangent** relation to an adjoining line, a **radius** or **diameter** dimension, a
**concentric** relation to another circle, or a **coincidence** of an arc endpoint with a
neighbouring segment so the profile stays closed.

Arcs are how a profile turns a rounded corner or a fillet-in-sketch: the arc's endpoints are shared
with the segments on either side, and tangency makes the transition smooth ($G^1$ continuous). A
circle alone is a common profile for a boss or a hole, revolved or extruded into a cylinder.
