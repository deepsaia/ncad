The Newton-Euler equations are the force-level statement of rigid-body dynamics: together they say how the *net force* on a body moves its center of mass and how the *net moment* changes its rotation. They are the natural governing law for **multibody dynamics (MBD)**, where a mechanism is modeled as a set of rigid (or flexible) bodies connected by joints and driven by forces, motors, springs, gravity, and contact. Unlike a purely kinematic description, which only says *how* parts can move, the Newton-Euler equations say what motion actually results from a given set of loads.

For a single rigid body the two equations split cleanly into translation and rotation. Newton's second law governs the center of mass \(c\), and Euler's equation governs rotation. Written about the center of mass they are

\[ \mathbf{F} = m\,\mathbf{a}_c, \qquad \mathbf{M}_c = \mathbf{I}_c\,\dot{\boldsymbol{\omega}} + \boldsymbol{\omega}\times\left(\mathbf{I}_c\,\boldsymbol{\omega}\right), \]

where \(\mathbf{F}\) is the resultant external force, \(m\) the mass, \(\mathbf{a}_c\) the acceleration of the center of mass, \(\mathbf{M}_c\) the resultant moment about the center of mass, \(\mathbf{I}_c\) the inertia tensor about the center of mass, and \(\boldsymbol{\omega}\) the angular velocity. The rotational equation is most compact when \(\mathbf{I}_c\) is expressed in a body-fixed frame, because then \(\mathbf{I}_c\) is constant; the nonlinear term \(\boldsymbol{\omega}\times(\mathbf{I}_c\boldsymbol{\omega})\) is the **gyroscopic (Euler) term** that couples the rotational axes and is responsible for effects like the tumbling of an asymmetric body and precession.

## Why the two equations are separate

The clean split into a translation law and a rotation law is a theorem, not an assumption. For a system of particles the total external force equals the rate of change of total linear momentum, which depends only on the center-of-mass motion; internal forces cancel in pairs by Newton's third law. The same cancellation applied to moments shows the total external moment equals the rate of change of angular momentum. Taking the reference point at the center of mass (or at a fixed point) removes cross terms and yields the standard forms above. This is why the center of mass and the inertia tensor about it are the two mass properties every MBD solver needs.

## From one body to a constrained system

A mechanism is many bodies whose motions are not independent: joints impose **constraints** such as a shared axis (revolute), a shared line (prismatic), or coincident points. Stacking the Newton-Euler equations for all bodies and appending the constraint equations \(\boldsymbol{\Phi}(\mathbf{q},t)=\mathbf{0}\) yields the constrained equations of motion, typically written with a constraint Jacobian \(\boldsymbol{\Phi}_{\mathbf{q}}\) and Lagrange multipliers \(\boldsymbol{\lambda}\) that represent the joint reaction forces:

\[ \mathbf{M}\,\ddot{\mathbf{q}} + \boldsymbol{\Phi}_{\mathbf{q}}^{\top}\boldsymbol{\lambda} = \mathbf{Q}, \qquad \boldsymbol{\Phi}(\mathbf{q},t)=\mathbf{0}. \]

Here \(\mathbf{M}\) is the system mass matrix, \(\mathbf{Q}\) collects applied and velocity-dependent (Coriolis/gyroscopic) forces, and the multipliers scale the constraint gradients so that the reactions do no net work on admissible motions. This is a **differential-algebraic system (DAE)**: differential equations for the motion coupled to algebraic constraints. Solvers integrate it forward in time, usually stabilizing the algebraic constraints (Baumgarte stabilization, projection, or index reduction) so that position and velocity constraints stay satisfied despite numerical drift.

## Where it matters

The Newton-Euler equations are the engine behind force-driven simulation: given actuator torques, contact loads, and gravity, they predict the resulting trajectory, and inversely, given a desired motion they yield the joint reactions and required actuator efforts (inverse dynamics for sizing motors, bearings, and structure). Efficient recursive formulations propagate velocities outward from a base and forces inward across the joints, giving \(O(n)\) algorithms for chains that are the practical basis of real-time robotics and machinery simulation. The accuracy of any such result rests entirely on correct mass properties and a faithful constraint set, which is why the inertia tensor and the joint model are treated as first-class data alongside the equations themselves.
