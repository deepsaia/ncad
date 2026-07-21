Nonlinear structural analysis is required whenever the tidy assumptions behind \(\mathbf{K}\mathbf{u}=\mathbf{f}\) break down and stiffness itself depends on the solution. It is conventional to sort the sources of nonlinearity into three independent categories, because they arise from different physics and each demands its own formulation. A single simulation can, and often does, involve all three at once.

## The three sources

**Geometric nonlinearity** appears when displacements or rotations are large enough that equilibrium must be written on the deformed shape. Even with a linear-elastic material, this produces stress stiffening, snap-through of shallow arches and domes, follower loads (pressure that rotates with the surface), and buckling in the post-critical range. It is expressed with finite-strain measures such as the Green-Lagrange strain and its work-conjugate second Piola-Kirchhoff stress. **Material nonlinearity** is a nonlinear constitutive law: elastoplasticity (a yield surface, a flow rule setting the direction of plastic strain, and a hardening law), hyperelasticity for rubber-like materials (strain energy densities such as Neo-Hookean or Mooney-Rivlin), viscoelasticity and creep with time-dependent response, and progressive damage. **Contact and boundary nonlinearity** arises when the region of load transfer changes during the analysis: surfaces that open and close, unilateral (no-tension) constraints, and friction all switch the effective stiffness abruptly and make the response history-dependent.

## Solving: incremental-iterative equilibrium

Because stiffness varies, the load is applied in increments and each increment is iterated to equilibrium. The governing statement is that the residual (out-of-balance force) must vanish,

\[ \mathbf{r}(\mathbf{u}) = \mathbf{f}^{\text{ext}} - \mathbf{f}^{\text{int}}(\mathbf{u}) = \mathbf{0}, \]

solved by Newton-Raphson iteration \(\mathbf{K}_T\,\Delta\mathbf{u}=\mathbf{r}\), where the tangent stiffness \(\mathbf{K}_T=\partial \mathbf{f}^{\text{int}}/\partial \mathbf{u}\) is reassembled (fully or in a modified scheme) as the state evolves. Convergence is declared when force and displacement residuals fall below tolerance. Near limit points, where the load-displacement curve turns back on itself (snap-through, snap-back), plain load control fails and arc-length (Riks) methods, which treat the load factor as an unknown and advance along the equilibrium path, are used instead.

## Why it matters

The practical payoff is that nonlinear analysis predicts behavior a linear model cannot even represent: permanent set and residual stress after yielding, the true collapse load of a structure past its buckling point, the seating and load spreading of a bolted or contact joint, and the large deflections of gaskets, seals, and elastomeric mounts. It costs far more computationally and can fail to converge, so it is reserved for questions where linearity is genuinely violated, and its results are always checked against energy balance and mesh and increment refinement.
