Kinematic analysis answers where the parts go; dynamic analysis answers what internal loads are required to make them go there. In the constrained-multibody formulation those loads appear as **Lagrange multipliers**, and recovering them is the principal reason to escalate from a kinematic study to a full dynamic one. A kinematic simulation of a linkage gives positions, velocities, and accelerations but says nothing about the pin shear, bearing load, or bracket force transmitted through each joint; the multipliers supply exactly that.

## The augmented equations of motion

For generalized coordinates \(q\) with mass matrix \(M(q)\), applied and velocity-dependent generalized forces \(Q\), and constraint equations \(\Phi(q,t)=0\), the equations of motion are written in augmented (multiplier) form

\[ M(q)\,\ddot q + \Phi_q^{\mathsf T}\,\lambda = Q(q,\dot q,t), \qquad \Phi(q,t) = 0, \]

where \(\Phi_q = \partial\Phi/\partial q\) is the constraint Jacobian and \(\lambda\) is the vector of Lagrange multipliers. The term \(\Phi_q^{\mathsf T}\lambda\) is the **generalized constraint force**. Its structure encodes a physical principle: the rows of \(\Phi_q\) are gradients of the constraint functions, hence normals to the constraint manifold, so the reaction acts only in the directions the constraints forbid. Along any admissible (constraint-satisfying) virtual displacement \(\delta q\) we have \(\Phi_q\,\delta q = 0\), so the constraint force does no virtual work. This is d'Alembert's principle, and it is what guarantees the multipliers represent ideal workless reactions rather than an arbitrary force fit.

## From multipliers to physical joint loads

Each multiplier scales the reaction that enforces one scalar constraint equation. The generalized reaction associated with a given joint is \(Q^{c} = -\Phi_q^{\mathsf T}\lambda\) restricted to that joint's constraint rows; resolving it through the joint's kinematic definition yields the force and torque transmitted across the pair, expressed at a chosen point and in a chosen frame. Those are precisely the quantities downstream engineering needs: bearing capacity checks, fastener and pin sizing, weld and bracket stress, and fatigue spectra derived from the time history of the reaction. Because sign and normalization conventions differ between formulations, and because a raw multiplier is tied to how its constraint was scaled, the physically meaningful step is always to map \(\lambda\) back through the specific Jacobian to obtain a force at a point in a frame.

## Solving for the multipliers

The multipliers are not integrated as states; they are solved for algebraically at each instant. Differentiating the constraints to acceleration level and appending them to the equations of motion gives the linear saddle-point (Karush-Kuhn-Tucker) system

\[ \begin{bmatrix} M & \Phi_q^{\mathsf T} \\ \Phi_q & 0 \end{bmatrix} \begin{bmatrix} \ddot q \\ \lambda \end{bmatrix} = \begin{bmatrix} Q \\ \gamma \end{bmatrix}, \]

where \(\gamma = -\big(\dot\Phi_q\,\dot q + 2\,\Phi_{qt}\,\dot q + \Phi_{tt}\big)\) is the acceleration-level right-hand side. Solving this block system each step returns both the accelerations and the multipliers simultaneously. Its solvability rests on \(\Phi_q\) having full row rank (independent, non-redundant constraints); when constraints are redundant or the mechanism passes through a singular (locked or bifurcating) configuration, the Jacobian loses rank and the reactions become indeterminate, which is a genuine modeling signal and not merely a numerical nuisance.
