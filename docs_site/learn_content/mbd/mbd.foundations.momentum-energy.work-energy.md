**Work and energy** give a scalar view of dynamics that complements the vector momentum balance. Instead of tracking three components of force and moment, energy methods track a single number, the mechanical energy, whose changes are driven by the *work* that forces do along the actual path of motion. This scalar bookkeeping is often the fastest route to a result (no free-body diagram of constraint forces is needed when those forces do no work) and it provides one of the strongest invariants for validating a simulation.

The **work** done by a force \(\mathbf{F}\) as its point of application moves along a path is the line integral \(W = \int \mathbf{F}\cdot d\mathbf{s}\), and correspondingly a moment does work \(\int \mathbf{M}\cdot d\boldsymbol{\theta}\) through an angular displacement. The **work-energy theorem** states that the net work done on a rigid body equals the change in its **kinetic energy**, which for a rigid body separates into translational and rotational parts:

\[ T = \tfrac{1}{2}\,m\,\lVert\mathbf{v}_c\rVert^{2} + \tfrac{1}{2}\,\boldsymbol{\omega}^{\top}\mathbf{I}_c\,\boldsymbol{\omega}. \]

The rotational term uses the same inertia tensor that appears in Euler's equation, tying energy directly to mass properties. **Power** is the time rate of doing work, \(P = \mathbf{F}\cdot\mathbf{v} + \mathbf{M}\cdot\boldsymbol{\omega}\), and the net power delivered to a body equals \(dT/dt\); this relation is exactly what sizes an actuator, since an actuator must supply the peak power its motion demands, not merely the peak force.

## Conservative forces and energy conservation

A force is **conservative** if the work it does is path-independent, which means it derives from a potential, \(\mathbf{F} = -\nabla U\); gravity and ideal springs are the standard examples. For a system acted on only by conservative forces and workless constraints, the **total mechanical energy** is conserved:

\[ E = T + U = \text{constant}. \]

Ideal joints (frictionless, rigid) transmit constraint forces perpendicular to the allowed motion, so they do no work and drop out of the energy balance, which is why energy methods sidestep reaction forces entirely. Non-conservative effects, friction, damping, and driven actuators, appear as explicit work terms, and the general statement becomes \(\Delta(T+U) = W_{\text{non-conservative}}\).

## Where it matters

Energy is the basis of the **Lagrangian** formulation, in which the equations of motion follow from the kinetic and potential energies alone, giving a compact and coordinate-flexible alternative to writing Newton-Euler equations body by body. In numerical MBD, conservation of energy is a primary correctness check: for an undriven, undamped system the total energy should stay flat, and structure-preserving (symplectic or energy-momentum) integrators are chosen precisely because they bound energy drift over long runs where generic integrators would gain or bleed energy artificially. Practically, work-energy reasoning answers questions like how fast a mechanism arrives at a stop, what power an actuator must deliver through a stroke, how much energy a spring or flywheel stores, and how much heat friction dissipates, all without solving for the internal constraint forces.
