A **fillet** rounds a sharp edge into a smooth radiused blend, tangent to the two faces it joins.
Fillets remove stress concentrations, ease handling, aid mold release, and finish a part visually.
The feature selects one or more edges and replaces each with a rolling-ball surface of the given
radius.

<figure markdown="span">
<svg viewBox="0 0 300 130" width="300" role="img" aria-label="A sharp corner rounded by a fillet" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M 30 30 L 30 100 L 110 100"/>
  <text x="35" y="120" fill="currentColor" stroke="none" font-size="11">sharp</text>
  <path d="M 190 30 L 190 70 A 30 30 0 0 0 220 100 L 270 100"/>
  <text x="205" y="120" fill="currentColor" stroke="none" font-size="11">filleted (radius r)</text>
</svg>
<figcaption>A sharp edge (left) replaced by a tangent radius (right).</figcaption>
</figure>

## Radius, selection, and order

The common form is **constant radius** on selected edges. Advanced variants (variable-radius along
an edge, face fillets between two faces, full-round replacing a thin wall with a semicircle) shape
more complex blends.

Fillets are notoriously order-sensitive and among the most fragile kernel operations. Round edges
while the base solid is still simple, before booleans and holes complicate the topology; a late
fillet on a heavily-featured solid can produce an invalid B-rep or crash the kernel. Selecting
edges by a persistent, semantic reference (rather than a raw index) is what keeps a fillet attached
to the right edge across rebuilds.
