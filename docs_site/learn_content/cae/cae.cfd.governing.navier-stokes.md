The motion of a viscous fluid is governed by three conservation laws applied to a continuum: conservation of mass, momentum, and energy. Together these form the Navier-Stokes system. Mass conservation (the continuity equation) states that the rate of change of density in a control volume balances the net mass flux across its boundary:

\[ \frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{u}) = 0 \]

Momentum conservation is Newton's second law for a fluid parcel, balancing inertia against pressure gradients, viscous stresses, and body forces:

\[ \frac{\partial (\rho \mathbf{u})}{\partial t} + \nabla \cdot (\rho\, \mathbf{u} \otimes \mathbf{u}) = -\nabla p + \nabla \cdot \boldsymbol{\tau} + \rho \mathbf{f} \]

For a Newtonian fluid the deviatoric stress is linear in the strain rate, \( \boldsymbol{\tau} = \mu\left(\nabla \mathbf{u} + (\nabla \mathbf{u})^{\mathsf{T}}\right) - \tfrac{2}{3}\mu(\nabla \cdot \mathbf{u})\mathbf{I} \), where \( \mu \) is the dynamic viscosity. The relative importance of inertial to viscous forces is set by the Reynolds number \( Re = \rho U L / \mu \), the single most important dimensionless group in fluid dynamics: it decides whether a flow is smooth (laminar) or chaotic (turbulent) and controls how fine a mesh a simulation needs.

## Incompressible vs. compressible

The practical fork in the road is whether density can be treated as constant. When flow speeds are well below the local speed of sound, density variations are negligible and the flow is modeled as **incompressible**. The continuity equation collapses to a divergence-free constraint \( \nabla \cdot \mathbf{u} = 0 \), and the momentum equation simplifies to

\[ \frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u} = -\frac{1}{\rho}\nabla p + \nu \nabla^2 \mathbf{u} + \mathbf{f}, \qquad \nu = \mu/\rho \]

Here pressure is no longer a thermodynamic state variable but a Lagrange multiplier that enforces the incompressibility constraint; there is no independent equation for it, which is the source of the pressure-velocity coupling difficulty in numerics. The transition threshold is conventionally taken at a Mach number \( M = U/a \approx 0.3 \); below it, compressibility corrections change results by only a few percent.

Above roughly \( M \approx 0.3 \) the **compressible** formulation is required, and density becomes an active field linked to pressure and temperature through an equation of state (for an ideal gas, \( p = \rho R T \)). The energy equation must now be solved simultaneously with mass and momentum because kinetic energy, internal energy, and pressure work exchange freely; shock waves, expansion fans, and aerodynamic heating are all consequences of this coupling. Transonic, supersonic, and hypersonic aerodynamics, gas turbine internal flows, and rocket nozzles all live in this regime.

The two regimes also drive different numerical strategies. Incompressible solvers typically use a **pressure-based** approach (segregated predictor-corrector schemes such as pressure-projection or SIMPLE-family algorithms) that derive a pressure equation from the continuity constraint. Compressible solvers historically use a **density-based** approach that marches the coupled conservation laws forward in time and recovers pressure from the equation of state, though modern pressure-based methods have been extended to all speed ranges. Choosing the right formulation is the first and most consequential modeling decision in any CFD study: using an incompressible solver where compressibility matters silently discards the physics of shocks and density-driven buoyancy, while using a compressible solver at very low Mach number leads to severe stiffness and slow convergence.
