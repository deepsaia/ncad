Many multibody systems are most naturally described with more coordinates than degrees of freedom, together with algebraic equations that tie those coordinates together. When a system with coordinate vector \(q\in\mathbb{R}^{n}\) is subject to \(m\) independent holonomic constraints \(\boldsymbol{\Phi}(q,t)=\mathbf{0}\), the constraint forces that enforce them are, by the principle of virtual work, orthogonal to the admissible directions. That orthogonality is exactly what the Lagrange-multiplier construction encodes: each scalar constraint contributes a reaction of the form \(\boldsymbol{\Phi}_q^{\top}\lambda\), directed along the constraint gradient, with the multipliers \(\lambda\in\mathbb{R}^{m}\) fixing their magnitudes.

## Augmented equations of motion

Adjoining the multipliers to the equations of motion gives the constrained (descriptor) form

\[ \mathbf{M}(q)\,\ddot q + \boldsymbol{\Phi}_q^{\top}\,\lambda = \mathbf{Q}, \qquad \boldsymbol{\Phi}(q,t) = \mathbf{0}, \]

where \(\boldsymbol{\Phi}_q = \partial\boldsymbol{\Phi}/\partial q\) is the constraint Jacobian and \(\mathbf{Q}\) collects applied and velocity-dependent forces. Physically, \(\boldsymbol{\Phi}_q^{\top}\lambda\) *is* the set of joint reaction forces, so unlike the minimal-coordinate approach this formulation delivers those reactions as part of the solution. The system as written is a differential-algebraic equation (DAE) of index 3.

## Reducing the index and closing the system

To solve the DAE numerically one differentiates the position constraint twice in time to expose the accelerations. This produces the acceleration-level constraint \(\boldsymbol{\Phi}_q\,\ddot q = \boldsymbol{\gamma}\), where \(\boldsymbol{\gamma} = -\big(\dot{\boldsymbol{\Phi}}_q\,\dot q + 2\boldsymbol{\Phi}_{qt}\dot q + \boldsymbol{\Phi}_{tt}\big)\). Together with the balance law it forms the symmetric saddle-point (KKT) system solved at each instant,

\[ \begin{bmatrix} \mathbf{M} & \boldsymbol{\Phi}_q^{\top} \\ \boldsymbol{\Phi}_q & \mathbf{0} \end{bmatrix} \begin{bmatrix} \ddot q \\ \lambda \end{bmatrix} = \begin{bmatrix} \mathbf{Q} \\ \boldsymbol{\gamma} \end{bmatrix}. \]

The left-hand matrix is nonsingular whenever \(\mathbf{M}\) is positive definite and \(\boldsymbol{\Phi}_q\) has full row rank; a rank deficiency in \(\boldsymbol{\Phi}_q\) signals redundant or singular constraints and a locally uncontrollable configuration. Because integrating only the acceleration-level form lets the original position and velocity constraints drift away from zero due to accumulated numerical error, practical solvers add a correction: Baumgarte stabilization replaces \(\boldsymbol{\gamma}\) with \(\boldsymbol{\gamma} - 2\alpha\dot{\boldsymbol{\Phi}} - \beta^{2}\boldsymbol{\Phi}\), turning constraint violation into a damped second-order system, while projection or coordinate-partitioning methods re-impose the constraints exactly at each step.

The same machinery extends to velocity-level (Pfaffian) constraints of the form \(\mathbf{A}(q)\,\dot q = \mathbf{0}\) that are not integrable, the nonholonomic case exemplified by rolling without slipping. There the multiplier still represents the reaction that enforces the velocity relation, but no position-level constraint exists to differentiate, so the constraint enters at the velocity and acceleration levels only. This multiplier-augmented, equation-and-constraint formulation is the standard basis for general-purpose multibody simulation, prized for handling closed kinematic loops and delivering reaction loads directly, at the cost of solving a larger, index-reduced DAE rather than a minimal set of ODEs.
