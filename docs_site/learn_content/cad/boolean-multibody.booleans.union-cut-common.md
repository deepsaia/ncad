**Boolean operations** combine two solids by set arithmetic on the volumes they occupy: **union**
(add, $A \cup B$), **cut/subtract** (remove, $A \setminus B$), and **common/intersect** (keep the
overlap, $A \cap B$). They are the backbone of solid modeling, most parts are unions of positive
features and cuts of negative ones.

<figure markdown="span">
<svg viewBox="0 0 340 110" width="350" role="img" aria-label="Union, cut, and intersect of two overlapping circles" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <g transform="translate(10,10)">
    <circle cx="35" cy="45" r="28"/><circle cx="60" cy="45" r="28"/>
    <text x="20" y="98" fill="currentColor" stroke="none" font-size="11">union</text>
  </g>
  <g transform="translate(130,10)">
    <circle cx="35" cy="45" r="28"/><circle cx="60" cy="45" r="28" stroke-dasharray="3 3" opacity="0.5"/>
    <text x="22" y="98" fill="currentColor" stroke="none" font-size="11">cut</text>
  </g>
  <g transform="translate(250,10)">
    <circle cx="35" cy="45" r="28" opacity="0.5" stroke-dasharray="3 3"/><circle cx="60" cy="45" r="28" opacity="0.5" stroke-dasharray="3 3"/>
    <path d="M 47 24 A 28 28 0 0 1 47 66 A 28 28 0 0 1 47 24 Z"/>
    <text x="20" y="98" fill="currentColor" stroke="none" font-size="11">intersect</text>
  </g>
</svg>
<figcaption>Union keeps both, cut removes the tool from the target, intersect keeps only the overlap.</figcaption>
</figure>

## Robustness

Booleans (BOP, boolean operations) are among the most powerful and most fragile kernel operations.
Tangent contacts, coincident faces, and near-degenerate overlaps can produce invalid results or
fail. A robust modeler validates every boolean output (checks the B-rep is sound) and converts a
silent failure into a typed, id-attributed error, rather than passing corrupt geometry downstream.
Authoring tools help: make a union's bodies overlap cleanly, keep a cut tool fully piercing, and
avoid exact face coincidence where a small overlap will do.
