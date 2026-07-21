The Hamiltonian formulation reorganizes mechanics from \(n\) second-order equations in the coordinates \(q\) into \(2n\) first-order equations in coordinates and momenta, trading the velocity \(\dot q\) for the **generalized (conjugate) momentum**

\[ p_i = \frac{\partial L}{\partial \dot q_i}. \]

Applying the Legendre transform to the Lagrangian defines the Hamiltonian as a function of the new variables,

\[ H(q,p,t) = \sum_{i=1}^{n} p_i\,\dot q_i - L(q,\dot q,t), \]

with the \(\dot q_i\) eliminated in favor of \(p_i\). For a scleronomic (time-independent constraints) system with kinetic energy quadratic in the velocities, \(H\) equals the total mechanical energy \(T+V\), and \(H = \tfrac12\,p^{\top}\mathbf{M}(q)^{-1}p + V(q)\) using the inverse mass matrix.

## Hamilton's canonical equations

The dynamics are then the symmetric first-order system

\[ \dot q_i = \frac{\partial H}{\partial p_i}, \qquad \dot p_i = -\frac{\partial H}{\partial q_i}, \]

known as Hamilton's canonical equations. The state \((q,p)\) lives in a \(2n\)-dimensional **phase space**, and the pair above defines a flow on it. Two consequences follow immediately: \(dH/dt = \partial H/\partial t\), so \(H\) is conserved whenever it has no explicit time dependence; and any coordinate absent from \(H\) (a cyclic coordinate) has a conserved conjugate momentum. The evolution of any observable \(f(q,p)\) is captured compactly by the Poisson bracket, \(\dot f = \{f,H\} + \partial f/\partial t\), which exposes the algebraic structure behind conservation laws and canonical transformations.

<svg viewBox="0 0 220 150" width="220" height="150" stroke="currentColor" fill="none" stroke-width="1.5"><line x1="20" y1="130" x2="200" y2="130"/><line x1="30" y1="140" x2="30" y2="15"/><text x="190" y="145" font-size="11" stroke="none" fill="currentColor">q</text><text x="10" y="22" font-size="11" stroke="none" fill="currentColor">p</text><ellipse cx="115" cy="75" rx="55" ry="38"/><ellipse cx="115" cy="75" rx="32" ry="22"/><polygon points="170,75 163,70 163,80" fill="currentColor" stroke="none"/></svg>

## Geometric structure and why it matters

Hamilton's equations have an underlying symplectic (area-preserving) geometry. Liouville's theorem states that the phase-space volume of any set of initial conditions is preserved by the flow, and the flow conserves the symplectic two-form. This is not a mere curiosity: it is the reason symplectic and variational integrators exist. Such integrators respect the geometric structure and therefore exhibit no secular energy drift over long simulations, an essential property for orbital mechanics, molecular dynamics, and long-horizon multibody integration where ordinary Runge-Kutta schemes would slowly gain or lose energy.

Beyond numerics, the canonical form is the natural setting for perturbation theory, action-angle variables and integrable systems, canonical transformations and Hamilton-Jacobi theory, and it is the classical structure that carries over into statistical and quantum mechanics. For constrained multibody systems the same ideas appear as constrained (Dirac) Hamiltonian dynamics, in which the momenta are subject to the constraint manifold and the flow is projected onto it. The formulation's cost, relative to the direct force-balance and generalized-speed methods, is that expressing \(H\) requires inverting the mass matrix and solving for the velocities, so it is chosen for its theoretical clarity and structure-preserving integration rather than for raw efficiency in generating equations.
