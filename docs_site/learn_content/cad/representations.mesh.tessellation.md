**Tessellation** converts an exact B-rep into a triangle mesh, approximating its curved surfaces
with flat facets. It is the bridge from the modeling kernel to everything that consumes triangles: a
GPU viewer, a collision check, a 3D-printing slicer.

<figure markdown="span">
<svg viewBox="0 0 300 120" width="300" role="img" aria-label="A smooth circle approximated by a coarse and a fine polygon" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="70" cy="60" r="40" opacity="0.4"/>
  <polygon points="70,20 105,45 92,90 48,90 35,45"/>
  <text x="45" y="115" fill="currentColor" stroke="none" font-size="11">coarse</text>
  <circle cx="220" cy="60" r="40" opacity="0.4"/>
  <polygon points="220,20 245,28 262,48 262,72 245,92 220,100 195,92 178,72 178,48 195,28"/>
  <text x="195" y="115" fill="currentColor" stroke="none" font-size="11">fine</text>
</svg>
<figcaption>The same exact curve sampled coarsely and finely: smaller deflection, more facets, closer fit.</figcaption>
</figure>

## Deflection controls fidelity

The key parameter is **deflection**: the maximum allowed gap between a triangle and the true
surface. A **linear** deflection bounds the chordal distance; an **angular** deflection bounds the
turn between adjacent facets on a curve. Tighter deflection means more triangles and a closer
approximation, the tradeoff between visual quality and mesh size.

Tessellation is a one-way, lossy projection: it samples the exact geometry, it never replaces it.
Measurements, booleans, and export to manufacturing run on the B-rep; the mesh is generated only at
the display or simulation boundary, with a deflection tuned to the purpose. Deterministic
tessellation (fixed deflection) also matters for reproducible viewer output and golden-image tests.
