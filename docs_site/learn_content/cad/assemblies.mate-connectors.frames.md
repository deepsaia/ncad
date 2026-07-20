A **mate connector** is a named coordinate frame on a part, an origin plus an orientation, that
serves as an attachment point in an assembly. Instead of mating raw faces and edges (fragile under
edits), a part publishes connectors ("tip", "pivot", "bore_axis") that assemblies reference by name.

<figure markdown="span">
<svg viewBox="0 0 300 120" width="300" role="img" aria-label="A part with two named connector frames" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="60" y="40" width="180" height="35"/>
  <g stroke-width="2">
    <line x1="80" y1="57" x2="110" y2="57"/><line x1="80" y1="57" x2="80" y2="27"/>
    <line x1="220" y1="57" x2="250" y2="57"/><line x1="220" y1="57" x2="220" y2="27"/>
  </g>
  <text x="70" y="95" fill="currentColor" stroke="none" font-size="11">pivot</text>
  <text x="210" y="95" fill="currentColor" stroke="none" font-size="11">tip</text>
</svg>
<figcaption>A link publishing two connector frames (origin + axes) that joints attach to.</figcaption>
</figure>

## Why connectors, not faces

A connector is defined *on the part*, in the part's own frame, resolved through the persistent
reference layer, so it stays put when the part is re-featured. An assembly then relates connectors:
"join instance A's `tip` to instance B's `pivot`". This decouples the assembly from the part's
internal topology, an edit to the part that renumbers faces does not break the assembly, because the
assembly named a connector, not a face.

Connectors carry a full frame (position and orientation), so a mate can align not just a point but a
direction and a roll. They are the stable interface between a part and the assemblies that use it,
and the anchor points that joints turn into degrees of freedom.
