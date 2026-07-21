The augmented equations of a constrained multibody system are not an ordinary differential equation (ODE). They are a **differential-algebraic equation (DAE)**, because alongside the differential relations for the coordinates sits a purely algebraic relation, the constraint \(\Phi(q,t)=0\), and the multiplier vector \(\lambda\) appears with no derivative of its own. \(\lambda\) is fixed implicitly by the requirement that the constraint continue to hold, not by an evolution equation. This mixed structure is what makes constrained dynamics numerically distinct from unconstrained dynamics, and the key descriptor of the difficulty is the **index**.

## Differentiation index

The differentiation index is the number of times the algebraic equations must be differentiated with respect to time before the system can be rearranged into an explicit ODE for all unknowns, including \(\lambda\). Higher index means the algebraic part is more deeply hidden and the problem is harder and more sensitive. Writing the constrained equations of motion at the position level,

\[ M\,\ddot q + \Phi_q^{\mathsf T}\lambda = Q, \qquad \Phi(q,t) = 0, \]

yields a DAE of **index 3**. This is the canonical form for a mechanism modeled with dependent (Cartesian) coordinates and joint constraints.

## Index reduction by differentiation

Differentiating the constraint peels away one index at a time and exposes the constraint content at successively higher derivative levels:

\[ \Phi(q,t) = 0 \quad\text{(position level, index 3)}, \]
\[ \dot\Phi = \Phi_q\,\dot q + \Phi_t = 0 \quad\text{(velocity level, index 2)}, \]
\[ \ddot\Phi = \Phi_q\,\ddot q + \big(\dot\Phi_q\,\dot q + 2\Phi_{qt}\dot q + \Phi_{tt}\big) = 0 \quad\text{(acceleration level, index 1)}. \]

At the acceleration level the constraint becomes a linear relation in \(\ddot q\) that combines with the equations of motion to form the solvable saddle-point system used to advance the state. This reduction is why most implementations integrate the index-1 form.

## Why the index matters numerically

High-index DAEs are treacherous for standard solvers. As index rises, error is amplified: a perturbation can be differentiated back into the solution, and effective sensitivity scales roughly like a negative power of the step size, so naive discretizations of an index-3 system are unstable or fail to converge. The deeper problem is **drift**. When the system is reduced to the acceleration level and integrated, only \(\ddot\Phi = 0\) is being enforced directly; the underlying position constraint \(\Phi=0\) and velocity constraint \(\dot\Phi=0\) are merely consequences of exact integration. Because numerical integration is not exact, truncation and rounding error accumulate and the trajectory slowly leaves the constraint manifold, joints appear to pull apart or interpenetrate even though the acceleration equation is satisfied at every step. Index reduction therefore trades one difficulty for another: it makes the system tractable for ODE-style integrators but introduces the drift that constraint stabilization and projection methods exist to control.
