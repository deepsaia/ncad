A **coincidence constraint** forces two points (or a point and a curve) to occupy the same
location. It is the most fundamental geometric constraint: it is what joins two segments into a
corner, closes a profile loop, and pins a vertex onto an axis or another entity.

Variants include **point-on-point** (two endpoints merge), **point-on-line** (a point must lie
somewhere along a line), and **point-on-curve** (a point constrained to an arc or spline). Each
removes one or two degrees of freedom from the sketch.

<figure markdown="span">
<svg viewBox="0 0 320 130" width="340" role="img" aria-label="Coincidence merging two endpoints" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="30" y1="40" x2="120" y2="60"/>
  <line x1="150" y1="95" x2="240" y2="70"/>
  <text x="250" y="60" fill="currentColor" stroke="none" font-size="12">before</text>
  <line x1="40" y1="110" x2="130" y2="110"/>
  <line x1="130" y1="110" x2="210" y2="70"/>
  <circle cx="130" cy="110" r="5" fill="currentColor"/>
  <text x="220" y="95" fill="currentColor" stroke="none" font-size="12">after (coincident)</text>
</svg>
<figcaption>Two loose segments (top) become a closed corner once their endpoints are made coincident (bottom).</figcaption>
</figure>

## Why it is the backbone of a sketch

A profile that a feature can extrude or revolve must be a **closed loop**: every segment's end
coincides with the next segment's start. Coincidence is what guarantees that closure symbolically,
rather than relying on two endpoints happening to have equal coordinates (which floating-point edits
would break). Because shared endpoints are one point entity, most coincidences are implicit; explicit
coincidence constraints handle the cases where separate entities must be tied together.
