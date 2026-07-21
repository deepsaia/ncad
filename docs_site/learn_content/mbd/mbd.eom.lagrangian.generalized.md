Lagrangian dynamics recasts the equations of motion in terms of a minimal set of independent coordinates rather than Cartesian positions and their constraint forces. A system with \(n\) degrees of freedom is described by generalized coordinates \(q_1,\dots,q_n\), which may be angles, arc lengths, or any convenient parameters. The central object is the Lagrangian, the difference between kinetic and potential energy,

\[ L(q,\dot q,t) = T(q,\dot q,t) - V(q,t), \]

both scalars, so the whole formulation is coordinate-free and invariant under smooth changes of coordinates.

## The Euler-Lagrange equations and their origin

The equations of motion follow from Hamilton's principle, which states that the physical trajectory makes the action \(\int_{t_1}^{t_2} L\,dt\) stationary among neighboring paths with fixed endpoints, \(\delta\!\int L\,dt = 0\). Carrying out that variation gives one second-order equation per coordinate,

\[ \frac{d}{dt}\!\left(\frac{\partial L}{\partial \dot q_i}\right) - \frac{\partial L}{\partial q_i} = Q_i, \qquad i = 1,\dots,n, \]

where \(Q_i\) is the generalized force collecting all non-conservative and applied effects not already captured in \(V\). The decisive practical payoff is that ideal (workless) constraint forces, joint reactions, normal contact forces on smooth surfaces, and the like, do no virtual work along admissible motions and therefore drop out entirely. One writes only energies and the applied loads, and the reactions never enter.

## The manipulator / mass-matrix form

Because kinetic energy of a mechanical system is quadratic in the velocities, \(T = \tfrac12\,\dot q^{\top} \mathbf{M}(q)\,\dot q\), the Euler-Lagrange equations collapse into the standard second-order form used throughout multibody dynamics and robotics,

\[ \mathbf{M}(q)\,\ddot q + \mathbf{C}(q,\dot q)\,\dot q + \mathbf{g}(q) = \boldsymbol{\tau}. \]

Here \(\mathbf{M}(q)\) is the symmetric positive-definite mass (inertia) matrix, \(\mathbf{g}(q) = \partial V/\partial q\) is the gravity/conservative term, and \(\mathbf{C}(q,\dot q)\,\dot q\) gathers the velocity-dependent Coriolis and centrifugal terms. The entries of \(\mathbf{C}\) are the Christoffel symbols of the first kind built from derivatives of \(\mathbf{M}\), \(C_{ij} = \sum_k \tfrac12\big(\partial_k M_{ij} + \partial_j M_{ik} - \partial_i M_{jk}\big)\dot q_k\), and the choice can be made so that \(\dot{\mathbf{M}} - 2\mathbf{C}\) is skew-symmetric, a property that mirrors energy conservation and is heavily used in control.

Lagrangian dynamics is the workhorse for deriving symbolic equations of motion for mechanisms and open kinematic chains, for building reduced-order models, and for control design where the \(\mathbf{M},\mathbf{C},\mathbf{g}\) structure is exploited directly. Its limitation is the flip side of its strength: because constraint forces are eliminated, joint reactions must be recovered by a separate step, and for large systems the symbolic differentiation of \(L\) becomes unwieldy compared with the recursive force-balance and generalized-speed formulations.
