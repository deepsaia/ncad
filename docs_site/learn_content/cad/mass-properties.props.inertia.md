The **moment of inertia** describes how a body's mass is distributed about axes, its resistance to
angular acceleration. It is captured by the $3\times3$ **inertia tensor** about the centre of mass:

\[
I = \begin{bmatrix} I_{xx} & -I_{xy} & -I_{xz} \\ -I_{xy} & I_{yy} & -I_{yz} \\ -I_{xz} & -I_{yz} & I_{zz} \end{bmatrix},
\]

with diagonal moments $I_{xx} = \iiint (y^2 + z^2)\,\rho\, dV$ (and cyclic) and off-diagonal
products of inertia. Diagonalizing $I$ gives the **principal axes** and **principal moments**, the
orientation in which the products vanish.

## Computed from the solid

The kernel integrates the inertia tensor over the exact B-rep (again via surface integrals),
referenced to the centre of mass, then extracts the principal moments and axes. These are exact for
the modeled geometry and density.

## Why it matters

Inertia is what turns a static part into a dynamic one. A motion or multibody-dynamics solve needs
each body's mass, centre of mass, and inertia tensor to compute accelerations, reaction forces, and
oscillation periods; a mechanism cannot be simulated without physically consistent inertias. Because
ncad computes these from the same model the geometry lives in, the properties a physics backend
needs are produced directly, no separate mass model to maintain.
