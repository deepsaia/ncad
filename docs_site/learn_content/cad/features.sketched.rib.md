A **rib** (web or stiffener) turns an open sketch curve into a thin, walled feature that braces a
part, the reinforcing gussets between a boss and a base, the stiffening webs in a cast bracket. From
a single open profile the feature thickens the curve to a wall and extends it until it meets
surrounding material.

<figure markdown="span">
<svg viewBox="0 0 300 140" width="320" role="img" aria-label="A rib bracing a boss to a base plate" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="30" y="100" width="240" height="25"/>
  <rect x="130" y="30" width="40" height="70"/>
  <polygon points="130,100 130,60 60,100" opacity="0.6"/>
  <text x="60" y="90" fill="currentColor" stroke="none" font-size="11">rib</text>
</svg>
<figcaption>An open profile thickened into a wall and grown until it meets the boss and the plate.</figcaption>
</figure>

## Open profile, thickness, and extent

Unlike extrude (which needs a *closed* profile), a rib is built from an **open** curve: the feature
gives it a wall thickness (symmetric about the sketch or to one side) and a growth direction, then
trims it against the existing solid so the rib fuses flush. The result must overlap the parts it
joins, a rib that stops short leaves a disjoint sliver and the fuse fails.

Ribs are order-sensitive: they come after the walls they brace exist, so the trim has material to
meet. A native rib with an until-material extent auto-trims to the surrounding solid; where that is
unavailable, a boolean-trim of a thicker blade stands in.
