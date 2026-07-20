A **hole** feature drills one or more holes at specified positions, capturing the full engineering
intent of a fastener hole rather than just a cylindrical cut. A **hole wizard** encodes standard
hole types so a single feature produces a correctly-dimensioned, standards-compliant hole.

<figure markdown="span">
<svg viewBox="0 0 300 130" width="300" role="img" aria-label="Simple, counterbored, and countersunk holes in section" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="20" y="20" width="260" height="90" opacity="0.15" fill="currentColor" stroke="none"/>
  <path d="M 55 20 L 55 100 M 75 20 L 75 100"/>
  <text x="45" y="122" fill="currentColor" stroke="none" font-size="10">simple</text>
  <path d="M 135 20 L 135 45 L 145 45 L 145 100 M 175 20 L 175 45 L 165 45 L 165 100"/>
  <text x="128" y="122" fill="currentColor" stroke="none" font-size="10">counterbore</text>
  <path d="M 225 20 L 235 40 L 235 100 M 265 20 L 255 40 L 255 100"/>
  <text x="222" y="122" fill="currentColor" stroke="none" font-size="10">countersink</text>
</svg>
<figcaption>Section through a plate: a simple hole, a counterbore, and a countersink.</figcaption>
</figure>

## Types and sizing

The feature covers **simple**, **counterbore** (a flat recess for a cap screw head), **countersink**
(a conical recess for a flat-head screw), and **tapped/threaded** holes. ISO-metric sizing takes a
size (`M6`) and a fit class (close/normal/loose/tapped) and looks up the correct clearance diameter,
so the author states intent ("M6 normal fit") not raw numbers. A cosmetic thread tag records thread
data without modeling every helix.

Positions are given explicitly or driven by a pattern (a bolt circle). Because a hole subtracts
material, it comes after the solid it pierces exists, and its edges (the drilled circle) become
references that later chamfers or countersinks can select.
