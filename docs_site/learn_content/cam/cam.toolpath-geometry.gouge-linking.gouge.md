A toolpath that is geometrically correct in plan view can still ruin a part if the cutter removes material it should not. **Gouging** is over-cut into the design surface; **collision** is contact between non-cutting structure (the shank, holder, spindle, or fixture) and the workpiece. Detecting and preventing both is a correctness requirement, not a nicety, and it splits into two regimes: *local* interference near the contact point and *global* interference with distant geometry.

## Local gouging and curvature matching

Local gouging happens when the tool's curvature at the contact exceeds the surface's curvature there, so the cutter digs below the surface on either side of the contact point. For a rotationally symmetric cutter to avoid gouging a concave region, its effective radius must not exceed the minimum radius of curvature of the surface:

\[ r_{\text{eff}} \;\le\; \frac{1}{\kappa_{\max}} = \rho_{\min}, \]

where \(\kappa_{\max}\) is the maximum principal curvature (most concave direction) of the surface at the contact. In multi-axis machining, *curvature-matched* strategies tilt the tool so the curvature of the tool's contact ellipse aligns with and stays below the surface curvature, maximizing the effective tool footprint without gouging.

## Global interference and configuration space

Global gouging and holder collisions require checking the whole tool assembly against the whole model, not just the local patch. One clean formulation is the **configuration-space (C-space)** view: describe each admissible tool state (position, and for multi-axis also orientation) as a point in a configuration space, mark as forbidden every state in which any part of the tool assembly penetrates the part, and require the toolpath to lie in the free region. Equivalently, one can work with the **inverse tool offset**: offset the design surface outward by the tool's shape (a Minkowski operation) so that keeping the tool's reference point on the offset guarantees, by construction, that the tool contacts but never penetrates the surface. Drop-cutter is a special case of this offset idea and is gouge-free for the cutting tip automatically.

## Holder reach and setup consequences

Sweeping the holder and shank volume against the part answers a distinct question: the minimum tool stickout (gauge length) needed to reach a pocket floor without the holder rubbing the walls, and which regions are simply unreachable and must be left for a longer or smaller tool, a different tool axis, or another setup. This analysis feeds tool selection and rest machining directly: a region flagged as holder-inaccessible with the current tool becomes a target for the next operation. Robust checks use conservative bounding volumes plus a z-map or swept-volume test, trading a little pessimism for the guarantee that a path certified collision-free really is.
