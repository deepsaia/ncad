A **draft** tapers a face by a small angle about a neutral plane so a molded or cast part can
release from its tooling. Without draft, vertical walls bind against the mold; a degree or two of
taper lets the part pull free. Draft is essential to any part destined for injection molding, die
casting, or sand casting.

<figure markdown="span">
<svg viewBox="0 0 300 130" width="300" role="img" aria-label="A vertical wall tapered by a draft angle" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="40" y="30" width="50" height="80"/>
  <text x="40" y="125" fill="currentColor" stroke="none" font-size="11">no draft</text>
  <path d="M 200 30 L 240 30 L 255 110 L 185 110 Z"/>
  <line x1="185" y1="110" x2="255" y2="110" stroke-dasharray="4 3" opacity="0.5"/>
  <text x="185" y="125" fill="currentColor" stroke="none" font-size="11">drafted (neutral plane at base)</text>
</svg>
<figcaption>Walls tapered about a neutral plane so the part lifts out of the mold.</figcaption>
</figure>

## Neutral plane, angle, and the planar-only rule

A draft needs a **neutral plane** (the section that keeps its size, the parting line), a **pull
direction**, and an **angle**. Faces above/below the neutral plane taper outward/inward accordingly.

Draft applies to **planar faces only**, a taper angle is undefined on a cylinder or sphere, so the
feature filters selected faces to planar ones and errors if none remain. It also requires the target
to be a single solid. Order matters both ways: fillet before draft (a draft would rotate corner
edges out of a "vertical" selection), and draft while faces are still simple planar walls, before
booleans mix in curved and drilled faces.
