A **conic** is a curve obtained by slicing a cone: the **ellipse**, **parabola**, and
**hyperbola** (the circle is a special ellipse). In sketching, the ellipse is the common one, a
closed oval defined by a centre, a major radius, and a minor radius, used for oblique holes,
cam profiles, and stylized fillets.

The general planar conic satisfies a quadratic in $x$ and $y$:

\[
A x^2 + B xy + C y^2 + D x + E y + F = 0,
\]

and modeling kernels also represent conics in the projective **rho** form (a control polygon plus a
tension parameter $\rho \in (0,1)$), where $\rho < 0.5$ gives an ellipse, $\rho = 0.5$ a parabola,
and $\rho > 0.5$ a hyperbola. The rho form is how a conic edge is authored as a single tensioned arc
between two endpoints with a shoulder apex, matching how NX/Creo model a conic.

## In sketching

An ellipse contributes its centre, its axis orientation, and two radii as solver unknowns; a
dimension pins each radius and a constraint fixes the axis direction. Conics fill the gap between
arcs (constant curvature) and free splines (arbitrary curvature): they give a smooth,
mathematically exact curve whose shape is controlled by a couple of parameters rather than a
control net.
