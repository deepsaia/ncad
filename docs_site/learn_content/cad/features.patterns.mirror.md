A **mirror** feature reflects geometry across a plane, producing a symmetric copy. It is the
natural tool for symmetric parts: model one half (or one side's features) and mirror to complete
it, a left-and-right bracket pair, a symmetric rib layout, matched mounting ears.

<figure markdown="span">
<svg viewBox="0 0 300 120" width="320" role="img" aria-label="A feature mirrored across a plane" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="150" y1="10" x2="150" y2="110" stroke-dasharray="6 4" opacity="0.6"/>
  <text x="140" y="120" fill="currentColor" stroke="none" font-size="10">mirror plane</text>
  <path d="M 60 40 L 110 40 L 110 90 L 90 90 L 90 60 L 60 60 Z"/>
  <path d="M 240 40 L 190 40 L 190 90 L 210 90 L 210 60 L 240 60 Z" opacity="0.6"/>
</svg>
<figcaption>The original (left) reflected across the plane to its mirror image (right).</figcaption>
</figure>

## Feature mirror versus body mirror

Two flavors: a **feature mirror** copies selected features (their sketches and operations) to the
other side of the plane, so the copy stays parametric and updates with the original; a **body
mirror** reflects the whole running solid. Like a pattern, mirror copies the running result and is
placed after the geometry it reflects.

A mirror across a plane the geometry *touches* fuses the reflection into one solid (a full symmetric
part); a mirror clear of the original leaves two bodies. Mirroring encodes symmetry as intent, one
edit to the master side propagates, which is more robust than modeling both halves independently.
