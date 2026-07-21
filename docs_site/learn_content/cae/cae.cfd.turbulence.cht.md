**Conjugate heat transfer (CHT)** is the simultaneous solution of heat transport in a fluid and one or more adjacent solids, with the two domains coupled at their shared interface. It exists because in many real systems neither domain can be characterized without the other: the solid's temperature depends on how much heat the fluid carries away, and the fluid's thermal boundary layer depends on the solid's surface temperature. Treating either side with an assumed boundary condition (a fixed wall temperature or a prescribed heat-transfer coefficient) forces the analyst to guess the very quantity the simulation should predict. CHT removes that guess by solving both fields together.

In the fluid the energy equation carries convection and conduction (and often viscous dissipation and radiation),

\[ \rho c_p \left( \frac{\partial T}{\partial t} + \mathbf{u}\cdot\nabla T \right) = \nabla\cdot(k\,\nabla T) + \dot{q} \]

while in the solid convection vanishes and pure conduction remains:

\[ \rho_s c_s \frac{\partial T}{\partial t} = \nabla\cdot(k_s\,\nabla T) + \dot{q}_s \]

## Interface coupling

The physics of the coupling lives entirely in two interface conditions. Temperature must be continuous across the fluid-solid boundary (no thermal contact resistance) and, by energy conservation, the normal heat flux leaving one domain must enter the other:

\[ T_f = T_s, \qquad k_f\,\nabla T_f\cdot\mathbf{n} = k_s\,\nabla T_s\cdot\mathbf{n} \]

These conditions replace the ad hoc wall boundary condition of an uncoupled analysis. The dimensionless group that governs whether coupling matters is the **Biot number** \( Bi = h L / k_s \), the ratio of internal conductive resistance in the solid to convective resistance at its surface. When \( Bi \gtrsim 0.1 \) the solid sustains a significant internal temperature gradient and a full conjugate treatment is warranted; when \( Bi \ll 0.1 \) the solid is nearly isothermal and a lumped or decoupled model may suffice.

## Coupling strategies and multiphysics context

Numerically, CHT is solved either **monolithically**, assembling fluid and solid energy equations into one linear system so the interface is satisfied implicitly, or in a **partitioned** (segregated) fashion, iterating between separate fluid and solid solvers and exchanging temperature and flux at the interface until convergence. Monolithic schemes are robust for tightly coupled problems but require a unified solver; partitioned schemes let specialized solvers be reused at the cost of possible under-relaxation and slower convergence when thermal properties differ sharply across the interface.

CHT is one instance of a broader **multiphysics** discipline in which distinct physical fields are coupled through shared interfaces or shared source terms. Related couplings include fluid-structure interaction (aerodynamic or hydrodynamic loads deforming a structure that in turn reshapes the flow), thermo-mechanical analysis (temperature fields driving thermal stress and distortion), and conjugate radiation. The same architectural choice recurs throughout: monolithic versus partitioned coupling, and matching field variables and their fluxes at the interface. CHT matters most where thermal management is design-critical (electronics cooling, gas-turbine blade and combustor liner cooling, heat exchangers, and engine components) precisely because these are cases where the solid's thermal response and the fluid's convective transport are inseparable.
