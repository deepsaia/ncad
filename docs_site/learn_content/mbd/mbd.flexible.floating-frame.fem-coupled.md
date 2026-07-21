FEM-coupled (or "fully coupled") flexible bodies drop the small-deformation assumption of the floating-frame method and instead retain a genuine finite-element description of the deformable body inside the multibody solver. Rather than projecting the motion onto a few mode shapes about a floating frame, the body's own nodal degrees of freedom participate directly in the system equations. That lets the formulation represent *geometrically nonlinear* behavior: large deflections, large rotations of individual elements, buckling, contact, and material nonlinearity, none of which the linearized modal approach can capture.

## Formulations

Several element families support this. Geometrically exact beam and shell theories (the Simo-Reissner beam is the canonical example) and corotational elements separate a large element-level rotation from small local strain. The Absolute Nodal Coordinate Formulation (ANCF) takes a different route: it uses global position vectors and their gradients (slopes) as nodal coordinates, interpolated in the inertial frame,

\[ \mathbf{r}(\mathbf{x},t) = \mathbf{S}(\mathbf{x})\,\mathbf{e}(t) \]

A key consequence is a *constant* mass matrix and the disappearance of Coriolis and centrifugal inertia terms, at the price of a strongly nonlinear elastic force vector. ANCF thus handles arbitrarily large rotation and deformation without the linearization that FFR requires, which is why it dominates in cable, belt, and tire modeling.

## Coupling strategies

Combining a structural FE model with the rigid-body and joint machinery can be done monolithically or by partitioning. In a monolithic scheme the flexible nodal coordinates and the multibody constraints are assembled into a single index-3 differential-algebraic system

\[ \mathbf{M}\ddot{\mathbf{q}} + \mathbf{f}_{\text{int}}(\mathbf{q}) + \mathbf{C}_{\mathbf{q}}^{\mathsf{T}}\boldsymbol{\lambda} = \mathbf{f}_{\text{ext}}, \qquad \mathbf{C}(\mathbf{q},t) = \mathbf{0}, \]

integrated with a stiff, constraint-respecting DAE method such as generalized-\(\alpha\), HHT, or a BDF scheme. In a *co-simulation* scheme a dedicated FE solver and an MBD solver run separately and exchange interface displacements and reaction forces at discrete communication points. Explicit (loosely coupled) exchange is cheap but can leak energy and go unstable when the interface is stiff, so implicit or corrected (Gauss-Seidel iterated) coupling is used in that regime, and the choice of which quantity to pass in which direction materially affects stability.

## Trade-offs and where it matters

The payoff is fidelity: FEM-coupled models capture nonlinear stiffening, large-displacement kinematics, and detailed stress fields that modal FFR simply cannot. The cost is many more degrees of freedom, a nonlinear (often non-symmetric) tangent matrix that must be re-formed and re-factored at each iteration, and careful attention to coupling stability and energy conservation. These models are chosen where the flexibility *is* the physics: slender cables and belts, tires and tracks, deploying membranes and antennas, rotor blades with large tip deflection, soft robotics, and biomechanics. Because this territory overlaps heavily with nonlinear finite-element analysis, many toolchains delegate the deformable-body solve to a dedicated FEA capability and couple it back, rather than reimplementing a full nonlinear structural solver inside the multibody core.
