**Tangent** and **concentric** constraints relate curved entities to their neighbours.

A **tangent** constraint forces a line or arc to meet a curve with matching direction at the contact
point, no corner, a smooth ($G^1$) transition. It is what blends a fillet arc into the straight
edges on either side, or lets a slot's end-cap arc flow into its parallel sides.

A **concentric** constraint forces two arcs or circles to share a centre. It aligns a counterbore
with its through-hole, a boss with its fillet, or nested rings on a flange.

<figure markdown="span">
<svg viewBox="0 0 320 140" width="340" role="img" aria-label="Tangent arc and concentric circles" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="20" y1="30" x2="90" y2="30"/>
  <path d="M 90 30 A 40 40 0 0 1 130 70"/>
  <line x1="130" y1="70" x2="130" y2="120"/>
  <text x="20" y="120" fill="currentColor" stroke="none" font-size="12">tangent fillet</text>
  <circle cx="245" cy="70" r="45"/>
  <circle cx="245" cy="70" r="25"/>
  <circle cx="245" cy="70" r="3" fill="currentColor"/>
  <text x="205" y="130" fill="currentColor" stroke="none" font-size="12">concentric</text>
</svg>
<figcaption>Tangency blends an arc smoothly into two lines; concentricity locks two circles to one centre.</figcaption>
</figure>

## Why they matter

These constraints express curvature intent that dimensions alone cannot: "these edges meet
smoothly" and "these features share an axis." Tangency is the sketch-level analogue of a
tangent-continuous fillet in 3D; concentricity is how coaxial features stay coaxial when the part is
re-dimensioned. Both remove degrees of freedom while keeping the shape well-behaved under edits.
