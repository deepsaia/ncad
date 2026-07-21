**Curvature** and **torsion** are the two scalar invariants that completely characterize the local shape of a space curve. Curvature measures how sharply the curve bends away from a straight line; torsion measures how it twists away from a plane. Both are defined with respect to arc length \(s\), so that they describe intrinsic shape independent of how the curve is parameterized.

**Curvature** \(\kappa\) is the rate at which the unit tangent \(\mathbf{T}\) turns as one moves along the curve:

\[ \kappa = \left\lVert \frac{d\mathbf{T}}{ds} \right\rVert \;\ge\; 0. \]

Its reciprocal \(R = 1/\kappa\) is the **radius of curvature**, the radius of the *osculating circle*, the unique circle that best matches the curve to second order at a point. A straight line has \(\kappa = 0\) (infinite radius); a circle of radius \(r\) has constant \(\kappa = 1/r\). For an arbitrary parameterization \(\mathbf{C}(u)\), curvature is computed without first reparameterizing by arc length using

\[ \kappa = \frac{\lVert \mathbf{C}' \times \mathbf{C}'' \rVert}{\lVert \mathbf{C}' \rVert^{3}}, \]

which for a plane graph \(y = f(x)\) reduces to the familiar \(\kappa = \lvert y'' \rvert / (1 + y'^2)^{3/2}\).

## Torsion and the fundamental theorem

**Torsion** \(\tau\) quantifies the rate at which the curve leaves its osculating plane, that is, how fast the plane containing the local bend rotates about the tangent. For a general parameterization,

\[ \tau = \frac{(\mathbf{C}' \times \mathbf{C}'') \cdot \mathbf{C}'''}{\lVert \mathbf{C}' \times \mathbf{C}'' \rVert^{2}}. \]

Unlike curvature, torsion carries a sign, distinguishing a right-handed from a left-handed twist, and it requires the third derivative because twisting is a third-order effect. A **planar curve has \(\tau \equiv 0\)** everywhere; nonzero torsion is exactly what makes a curve genuinely three-dimensional, as in a helix, which has both \(\kappa\) and \(\tau\) constant.

The reason these two functions matter so much is the **fundamental theorem of the local theory of curves**: given a curvature function \(\kappa(s) > 0\) and a torsion function \(\tau(s)\), there exists a curve realizing them, and it is unique up to a rigid motion (rotation and translation). In other words, \(\kappa(s)\) and \(\tau(s)\) together form a complete, position-free "DNA" of the curve's shape. This is the theoretical basis for representing and comparing shapes intrinsically.

In engineering practice, curvature is the workhorse quantity. Curvature plots and combs are used for **fairing**, detecting and smoothing unwanted wiggles in styling curves; curvature continuity governs high-quality surface blends and fillets; and curvature bounds constrain motion, since a machine following a path of curvature \(\kappa\) at speed \(v\) experiences centripetal acceleration \(v^2 \kappa\). Transition curves such as the clothoid (Euler spiral), whose curvature varies linearly with arc length, are used in road, rail, and tool-path design precisely to avoid the instantaneous curvature jump, and hence the acceleration shock, of joining a straight to a circular arc.
