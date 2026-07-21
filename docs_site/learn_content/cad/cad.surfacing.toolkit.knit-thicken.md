Trimming, knitting (sewing), and thickening are the three operations that turn a collection of independent parametric surfaces into a coherent, watertight solid or shell. They sit at the boundary between geometry (the surfaces and curves themselves) and topology (how those pieces connect), and each has its own governing idea and failure mode.

## Trim

A trimmed face keeps its underlying carrier surface \(S(u,v)\) defined over its full, often rectangular, parameter domain, but restricts the visible region to the interior of one or more trimming loops expressed in that parameter space. Convention is a single counter-clockwise outer loop plus zero or more clockwise inner loops that punch holes. Nothing is deleted from the carrier surface; evaluation and continuity queries still use the original \(S(u,v)\), while point-membership classification against the loops decides what is inside the face. This separation is essential because a later untrim, offset, or continuity check must reach back to the unbounded carrier.

## Knit / sew

Knitting assembles separate faces into a connected shell by detecting edges that are geometrically coincident within a fitting tolerance and merging them into a single shared topological edge. The result is a proper boundary representation in which faces reference common edges and vertices, so a walk across the model can cross from one face to its neighbour. If the resulting shell is closed (every edge is used by exactly two faces) and consistently oriented, it bounds a solid volume. The tolerance is the crux: too tight and real gaps from independent surface fits are rejected, too loose and distinct edges collapse incorrectly. Sewing is where geometric near-coincidence is promoted to exact topological identity.

## Thicken

Thickening offsets a surface or shell by a distance \(d\) along its unit normal to create a solid wall, generating the offset surface

\[
S_d(u,v) = S(u,v) + d\,\mathbf{n}(u,v).
\]

The offset is well behaved only while it stays clear of the focal (evolute) surface. Along a principal direction with principal curvature \(\kappa_i\), the offset's tangent scales by the factor \((1 - d\,\kappa_i)\); the offset point degenerates and the surface self-intersects when \(1 - d\,\kappa_i = 0\), i.e. when \(d = 1/\kappa_i\). Practically this means the offset stays regular only for \(|d| < 1/\kappa_{\max}\) on the concave side, where \(\kappa_{\max}\) is the largest principal curvature magnitude of the region. Robust thickening therefore detects and trims self-intersections rather than assuming a clean parallel copy.

These operations underpin thin-wall modeling: sheet-metal parts, plastic housings, and composite plies are all naturally authored as surfaces that are then knit and thickened into manufacturable solids. Getting the tolerance and curvature bounds right is what separates a manifold, machinable result from a shell riddled with tiny gaps or self-overlaps.
