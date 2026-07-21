In multibody dynamics the motion of a system of interconnected rigid or flexible bodies is governed by equations of motion that balance inertial effects against the forces acting on the system. Those forces divide cleanly into two families: **constraint forces**, which the joints generate implicitly to keep bodies connected, and **applied forces**, which are prescribed directly by the model. Gravity, external point loads, distributed loads reduced to a resultant, and applied torques all belong to the applied family. Getting them into the solver correctly is a matter of mapping each physical load onto the generalized coordinates that describe the system's configuration.

For a constrained system the equations of motion are commonly written in the augmented (Lagrange-multiplier) form

\[
\mathbf{M}\,\ddot{\mathbf{q}} + \boldsymbol{\Phi}_{\mathbf{q}}^{\mathsf T}\,\boldsymbol{\lambda} = \mathbf{Q}^{\mathrm a}(\mathbf{q},\dot{\mathbf{q}},t),
\]

where \(\mathbf{M}\) is the (generalized) mass matrix, \(\mathbf{q}\) the generalized coordinates, \(\boldsymbol{\Phi}_{\mathbf{q}}\) the constraint Jacobian, \(\boldsymbol{\lambda}\) the Lagrange multipliers (the joint reactions), and \(\mathbf{Q}^{\mathrm a}\) the vector of **generalized applied forces**. Every gravity term, external load, and driving torque enters through \(\mathbf{Q}^{\mathrm a}\); the multiplier term carries only the workless constraint reactions.

## Mapping a load to generalized forces

A concentrated force \(\mathbf{F}\) acting at a material point \(P\) does not contribute to \(\mathbf{Q}^{\mathrm a}\) directly; it must be projected through the kinematics of that point. Using the principle of virtual work, \(\delta W = \mathbf{F}^{\mathsf T}\,\delta\mathbf{r}_P\), and the fact that \(\delta\mathbf{r}_P = (\partial \mathbf{r}_P/\partial\mathbf{q})\,\delta\mathbf{q}\), the generalized force is

\[
\mathbf{Q}^{\mathrm a} = \left(\frac{\partial \mathbf{r}_P}{\partial \mathbf{q}}\right)^{\!\mathsf T}\mathbf{F}.
\]

The partial-derivative matrix is the point-location Jacobian; it distributes the force onto the translational and rotational coordinates according to where \(P\) sits relative to each body's reference frame. A **pure couple** (moment) \(\mathbf{T}\) performs no work under translation, so it maps only onto the rotational coordinates and produces no net force resultant, which is why offset loads and pure torques are treated separately in a robust formulation.

## Gravity as a special applied load

Gravity is the canonical always-present load. In a uniform field with acceleration vector \(\mathbf{g}\), each body \(i\) of mass \(m_i\) experiences a weight \(m_i\mathbf{g}\) acting at its center of mass. Its generalized-force contribution is \(\mathbf{J}_{c,i}^{\mathsf T}\,(m_i\mathbf{g})\), where \(\mathbf{J}_{c,i}\) is the Jacobian of the center-of-mass position. When the center-of-mass translation is itself a coordinate, this reduces to placing \(m_i\mathbf{g}\) on those coordinates and zero on the rotational ones, because gravity exerts no moment about the mass center. Equivalently, gravity is conservative and derives from the potential \(V = -\sum_i m_i\,\mathbf{g}^{\mathsf T}\mathbf{r}_{c,i}\).

Applied loads and gravity matter wherever a simulation must reproduce real weight, preload, or externally imposed effort: static-equilibrium (settling) solves, sag and droop under self-weight, actuator and bearing sizing from reaction extraction, and any transient where a body must accelerate under a known push. Practical fidelity hinges on consistent units, an explicitly defined "up" direction for \(\mathbf{g}\), correct sign conventions, and attaching each load to the intended point and body frame so that both the force resultant and its moment arm are represented.
