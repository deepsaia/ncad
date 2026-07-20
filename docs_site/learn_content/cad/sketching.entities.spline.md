A **spline** is a smooth freeform curve defined by a sequence of control or interpolation points.
Where lines and arcs give constant or zero curvature, a spline can follow an arbitrary, continuously
varying path, the entity for aerodynamic profiles, ergonomic edges, and cam laws.

The dominant form is the **NURBS** (Non-Uniform Rational B-Spline) curve, a weighted sum of
piecewise-polynomial basis functions:

\[
C(u) = \frac{\sum_{i} N_{i,p}(u)\, w_i\, P_i}{\sum_{i} N_{i,p}(u)\, w_i},
\]

where $P_i$ are control points, $w_i$ their weights, and $N_{i,p}$ the degree-$p$ B-spline basis
over a knot vector. NURBS subsume lines, arcs, and conics exactly (rational weights capture conics),
which is why a single curve type underlies most CAD geometry.

<figure markdown="span">
<svg viewBox="0 0 320 150" width="340" role="img" aria-label="A spline curve with its control polygon" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <polyline points="30,120 90,30 180,110 250,25 300,90" stroke-dasharray="4 3" opacity="0.5"/>
  <path d="M 30 120 C 70 50 120 70 180 90 C 220 102 260 60 300 90"/>
  <g fill="currentColor" stroke="none">
    <circle cx="30" cy="120" r="3"/><circle cx="90" cy="30" r="3"/>
    <circle cx="180" cy="110" r="3"/><circle cx="250" cy="25" r="3"/><circle cx="300" cy="90" r="3"/>
  </g>
</svg>
<figcaption>A spline (solid) shaped by its control polygon (dashed). Moving a control point deforms the curve locally.</figcaption>
</figure>

## In sketching

A spline's control points are solver variables, so dimensions and tangency constraints at its
endpoints let it join lines and arcs smoothly ($G^1$ or $G^2$). **Interpolating** splines pass
through their points (intuitive to author); **control-point** splines approximate them (better shape
control). Local control, moving one point perturbs only a nearby span, is what makes NURBS
practical to edit.
