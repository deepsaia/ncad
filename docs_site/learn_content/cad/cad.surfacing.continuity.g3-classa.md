\(G^3\) continuity extends the geometric-continuity hierarchy one step beyond curvature: it requires the rate of change of curvature to match across a join, so third-order geometric contact is preserved. For a curve this means \(d\kappa/ds\) is continuous at the seam, not merely \(\kappa\) itself. Read on a curvature comb, a \(G^2\) join has a continuous comb height but may kink in the comb's slope, whereas a \(G^3\) join makes the comb flow through with a continuous slope as well. For surfaces the analogous condition constrains the third-order cross-boundary behavior along the shared edge.

## What Class A means

Class A is a surface-quality bar rather than a single equation. It originates in automotive body styling and denotes the visible, cosmetic surfaces of a product: they must be at least \(G^2\), are frequently required to be \(G^3\), must be built from as few control points as the shape allows, and must exhibit clean, monotone curvature and defect-free reflection lines. The emphasis is aesthetic and perceptual: on a painted or reflective panel the human eye reads second- and third-order curvature defects directly through the distortion of reflected straight edges, so a mathematically valid but slightly uneven surface can still fail Class A inspection.

Achieving this quality is a fairing problem. The surface is refined to minimize a smoothness or bending-energy functional while honouring the boundary and continuity constraints, for example a strain-energy integral of the form

\[
E = \int_S \left(\kappa_1^2 + \kappa_2^2\right)\, dA,
\]

or, when the goal is a smoothly varying curvature rather than a merely small one, a functional penalizing the derivative of curvature such as \(\int (\dot\kappa)^2\, ds\) along characteristic curves. Reflection-line, isophote, and curvature-map inspection then drives iterative refinement until the surface is judged fair. Because the objective is subjective smoothness, the process couples numerical optimization with visual quality review.

Although the underlying differential geometry is standard, robust interactive \(G^3\) matching, reflection-line optimization, and production fairing tools are specialized capabilities and sit at the high end of surface modeling. The distinguishing factor is not the equations but the tooling that lets a designer enforce third-order continuity and clean reflections reliably and interactively across a large panel. Class A workflows matter most for exterior automotive and consumer-product surfaces, where reflection quality on the finished part is the acceptance criterion.
