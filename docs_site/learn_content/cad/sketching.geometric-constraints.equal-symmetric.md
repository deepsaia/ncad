**Equal** and **symmetric** constraints tie entities together so a single dimension drives several.

An **equal** constraint forces two lines to the same length, or two arcs/circles to the same
radius. Constrain the four sides of a shape equal and one length dimension makes it a square; make a
row of holes equal-radius and one diameter drives them all.

A **symmetric** constraint forces two entities to mirror across a centreline (a construction line or
axis): matching points stay equidistant on opposite sides. Editing one side moves the other
automatically.

<figure markdown="span">
<svg viewBox="0 0 320 140" width="340" role="img" aria-label="Symmetric points about a centreline" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="160" y1="15" x2="160" y2="125" stroke-dasharray="6 4" opacity="0.6"/>
  <text x="150" y="138" fill="currentColor" stroke="none" font-size="11">axis</text>
  <circle cx="90" cy="60" r="4" fill="currentColor"/>
  <circle cx="230" cy="60" r="4" fill="currentColor"/>
  <line x1="90" y1="60" x2="160" y2="60" stroke-dasharray="3 3" opacity="0.5"/>
  <line x1="160" y1="60" x2="230" y2="60" stroke-dasharray="3 3" opacity="0.5"/>
  <text x="60" y="90" fill="currentColor" stroke="none" font-size="11">d</text>
  <text x="195" y="90" fill="currentColor" stroke="none" font-size="11">d</text>
</svg>
<figcaption>Symmetry keeps the two points equidistant across the axis, so one edit updates both.</figcaption>
</figure>

## Why they encode intent

Equal and symmetric constraints capture *relationships* rather than absolute values, exactly the
intent a parametric model exists to preserve. A symmetric bracket that must stay symmetric under
edits gets a symmetry constraint, not two carefully matched dimensions that a later change could
desynchronize. They reduce the dimension count and make the sketch's meaning explicit to the next
editor.
