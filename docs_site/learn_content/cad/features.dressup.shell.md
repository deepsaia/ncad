A **shell** hollows a solid into a thin-walled shape of constant thickness, the feature for
enclosures, housings, bottles, and cast parts. It removes the interior, leaves walls of the
specified thickness, and opens selected faces so the cavity is accessible.

<figure markdown="span">
<svg viewBox="0 0 300 130" width="300" role="img" aria-label="A solid box shelled into an open thin-walled box" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="30" y="30" width="80" height="80"/>
  <text x="45" y="125" fill="currentColor" stroke="none" font-size="11">solid</text>
  <path d="M 190 30 L 270 30 L 270 110 L 190 110 Z"/>
  <path d="M 200 40 L 260 40 L 260 100 L 200 100" opacity="0.6"/>
  <text x="200" y="125" fill="currentColor" stroke="none" font-size="11">shelled (top open)</text>
</svg>
<figcaption>A solid (left) hollowed to a constant-thickness wall with its top face removed (right).</figcaption>
</figure>

## Thickness, open faces, and fragility

The parameters are the **wall thickness** and which **faces to open** (remove entirely). Inward
shelling (the common case) offsets the boundary inward by the thickness; a thickness larger than the
smallest local radius or wall makes the offset self-intersect, and the operation fails.

Shell is one of the most order-sensitive and fragile features: it should be applied while the solid
is still simple, before bosses, holes, and ribs complicate the topology. A late shell on a
feature-rich part frequently produces an invalid B-rep. This is why the feature-ordering discipline
puts base dress-up (shell, fillet, draft) early.
