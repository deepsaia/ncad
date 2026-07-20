A **chamfer** bevels a sharp edge into a flat angled face, the machinist's counterpart to a
fillet. Chamfers break sharp corners for safety and deburring, ease part insertion (a lead-in on a
shaft or hole), and prepare edges for welding.

<figure markdown="span">
<svg viewBox="0 0 300 130" width="300" role="img" aria-label="A sharp corner beveled by a chamfer" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M 30 30 L 30 100 L 110 100"/>
  <text x="35" y="120" fill="currentColor" stroke="none" font-size="11">sharp</text>
  <path d="M 190 30 L 190 70 L 230 100 L 270 100"/>
  <text x="205" y="120" fill="currentColor" stroke="none" font-size="11">chamfered</text>
</svg>
<figcaption>A sharp edge (left) replaced by a flat bevel (right).</figcaption>
</figure>

## Specifying the bevel

A chamfer is defined by one of a few schemes: a single **distance** (equal setback on both faces, a
45 degree bevel on a square corner), **two distances** (an asymmetric bevel), or a **distance and
angle**. The two-distance and distance-angle variants control the bevel precisely where a symmetric
45 degree cut is wrong.

Like fillets, chamfers are dress-up features applied late, but they are generally more robust than
fillets (a flat face is simpler for the kernel than a curved blend). Ordering still matters: a
chamfer selects edges by reference, and edges created by an earlier boolean or hole must exist
before the chamfer can target them.
