**Spatial-vector notation** is a systematic six-dimensional algebra for rigid-body dynamics, developed to write the equations of motion of mechanisms compactly and to derive efficient recursive algorithms. It is the dynamics-oriented sibling of screw theory: where classical screw theory emphasizes the *geometry* of lines and motions, spatial-vector notation is engineered so that Newton-Euler dynamics, inertias, momenta, and the accompanying differentiation rules all fit into one consistent 6D calculus, keeping the bookkeeping of angular and linear parts automatic.

## Two dual vector spaces

The notation carefully separates **motion vectors** \(M^6\) (twists, accelerations) from **force vectors** \(F^6\) (wrenches, momenta), which are dual spaces paired by the scalar product that yields power or work. A spatial velocity and spatial force are written, in a Plücker coordinate basis attached to a point \(O\),

\[
\hat{v} = \begin{bmatrix} \omega \\ v_O \end{bmatrix} \in M^6, \qquad
\hat{f} = \begin{bmatrix} n_O \\ f \end{bmatrix} \in F^6,
\]

with \(\hat{f}\cdot\hat{v}\) the power. Coordinate changes use a \(6\times6\) Plücker transform \({}^B\!X_A\) for motion vectors and its inverse-transpose \({}^B\!X_A^{*}\) for force vectors, guaranteeing the duality is preserved.

## Spatial inertia and the two cross products

Rigid-body inertia becomes a single symmetric positive-definite \(6\times6\) **spatial inertia** matrix \(I\) mapping a motion vector (velocity) to a force vector (momentum), \(\hat{h} = I\hat{v}\). Differentiation introduces two distinct spatial cross-product operators: \(\hat{v}\times\) acting on motion vectors and its dual \(\hat{v}\times^{*}\) acting on force vectors. With these, the equation of motion of a single rigid body is the strikingly compact

\[
\hat{f} = I\,\hat{a} + \hat{v}\times^{*} I\,\hat{v},
\]

where \(\hat{a}\) is the spatial acceleration and the second term captures all the Coriolis and gyroscopic effects that, in scalar notation, take pages to expand.

## Why it matters: O(n) recursive algorithms

The real payoff is algorithmic. Cast in spatial vectors, the dynamics of a kinematic tree decompose into recursions over the links. The **Recursive Newton-Euler Algorithm** computes inverse dynamics (the joint forces for a prescribed motion) in \(O(n)\) time by a velocity/acceleration sweep outward from the base followed by a force sweep back inward. The **Articulated-Body Algorithm** computes forward dynamics (the accelerations produced by given forces) in \(O(n)\), and the **Composite-Rigid-Body Algorithm** builds the joint-space inertia matrix in \(O(n^2)\). These are the workhorse routines behind real-time robot control, physics engines, and multibody simulators. Note that the coordinate ordering (angular-then-linear) and the strict motion/force distinction are conventions particular to this notation; keeping them straight is exactly what prevents the sign and transpose errors that plague ad-hoc 6D bookkeeping.
