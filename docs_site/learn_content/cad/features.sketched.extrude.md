**Extrude** sweeps a planar profile linearly along a direction (normally the sketch normal) to
create or modify a solid. It is the most common feature: a closed sketch becomes a prism of a given
depth.

<figure markdown="span">
<svg viewBox="0 0 300 150" width="320" role="img" aria-label="A profile extruded into a prism" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="40" y="80" width="70" height="45"/>
  <line x1="40" y1="80" x2="90" y2="45"/><line x1="110" y1="80" x2="160" y2="45"/>
  <line x1="40" y1="125" x2="90" y2="90"/><line x1="110" y1="125" x2="160" y2="90"/>
  <path d="M 90 45 L 160 45 L 160 90 L 90 90 Z" opacity="0.6"/>
  <line x1="200" y1="120" x2="200" y2="55" stroke-dasharray="4 3"/>
  <polygon points="200,55 196,65 204,65" fill="currentColor"/>
  <text x="208" y="90" fill="currentColor" stroke="none" font-size="12">distance</text>
</svg>
<figcaption>A closed profile swept along its normal by a distance becomes a prism.</figcaption>
</figure>

## End conditions

The depth is chosen by an **end condition**, not a bare flag: `blind` (a fixed distance),
`symmetric` (equal both ways about the sketch), `two_side` (independent distances each way),
`through_all` (pierces the whole body), `to_next` / `to_face` / `to_surface` (up to a referenced
geometry). Optional modifiers include a **draft** angle (taper the walls) and a **twist** (rotate
the profile over the length).

As an additive feature an extrude fuses into the running solid; the same operation cutting material
is a **pocket**. Getting the end condition right is a common source of silent wrong geometry, which
is why a robust modeler makes it explicit and rejects a flag that contradicts the chosen end.
