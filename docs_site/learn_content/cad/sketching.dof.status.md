A sketch is always in one of four **constraint states**, and a good sketcher reports which:

- **Well-defined** (fully constrained): zero remaining degrees of freedom, a unique solution. The
  intended, stable state.
- **Under-defined**: DoF remain, geometry can still be dragged. Not wrong, but the shape is not
  pinned, an edit elsewhere could move it unexpectedly.
- **Over-defined**: more independent constraints than DoF, so some conflict. The solver cannot
  satisfy them all; the offending constraints must be removed.
- **Redundant**: an extra constraint that duplicates one already implied (two ways of saying the
  same thing). Harmless to the solution but flagged, because it hides intent and can mask a real
  over-definition.

<figure markdown="span">
<svg viewBox="0 0 340 90" width="360" role="img" aria-label="Four sketch constraint states" xmlns="http://www.w3.org/2000/svg" font-size="11">
  <g fill="none" stroke="currentColor" stroke-width="2">
    <rect x="15" y="25" width="55" height="35"/>
    <rect x="105" y="25" width="55" height="35" stroke-dasharray="5 4"/>
    <rect x="195" y="25" width="55" height="35"/><line x1="195" y1="25" x2="250" y2="60"/>
    <rect x="285" y="25" width="45" height="35"/>
  </g>
  <g fill="currentColor" stroke="none" text-anchor="middle">
    <text x="42" y="78">well</text>
    <text x="132" y="78">under</text>
    <text x="222" y="78">over</text>
    <text x="307" y="78">redundant</text>
  </g>
</svg>
<figcaption>The four states a sketch reports: fully defined, under-defined, over-defined (conflict), and redundant.</figcaption>
</figure>

## Why surfacing the state matters

The state is a legibility layer over the raw solve: it tells the author *why* a sketch will or will
not behave, and which entities or constraints are responsible. Aiming for well-defined sketches is
the discipline that makes a parametric model predictable, an under-defined sketch is a latent
surprise, and an over-defined one will not rebuild.
