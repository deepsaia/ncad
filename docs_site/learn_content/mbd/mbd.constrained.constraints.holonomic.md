Constraints are the equations that couple the bodies of a mechanism, reducing the freedom each part would enjoy in isolation. A system described by \(n\) generalized coordinates \(q = (q_1, \dots, q_n)\) becomes *constrained* when relationships are imposed among those coordinates or their rates. The single most consequential way to classify such a relationship, because it dictates how far the motion can be reduced and which solution machinery applies, is whether the constraint is **holonomic** or **nonholonomic**.

## Holonomic constraints

A holonomic constraint is an algebraic relation among the coordinates, and possibly time,

\[ \Phi_i(q_1, \dots, q_n, t) = 0, \qquad i = 1, \dots, m. \]

When time appears explicitly the constraint is *rheonomic*; when it does not it is *scleronomic*. Each independent holonomic equation removes exactly one degree of freedom, so a system with \(m\) such constraints has \(n - m\) degrees of freedom, and its admissible configurations form a smooth manifold of that dimension embedded in the coordinate space. Crucially, holonomic constraints permit **coordinate reduction**: in principle one can solve for and eliminate \(m\) dependent coordinates and work in a minimal independent set. The standard kinematic joints of mechanism modeling, revolute, prismatic, cylindrical, spherical, and planar pairs, are all holonomic, which is why joint counts translate directly into a mobility (degree-of-freedom) count.

## Nonholonomic constraints

A nonholonomic constraint restricts velocities in a way that cannot be integrated into a relation among positions alone. Most such constraints are *Pfaffian*, linear in the velocities,

\[ \sum_{j=1}^{n} a_{ij}(q,t)\,\dot q_j + a_{i0}(q,t) = 0, \]

and the defining property is that this expression is **not** an exact (or integrable) differential of any function \(f(q,t)\). Such a constraint limits the directions in which the system may move at each instant, yet it does not shrink the set of reachable configurations. The archetypes are rolling without slipping (a wheel, disk, or sphere on a surface) and the knife-edge or skate. A coin rolling upright on a table cannot slide sideways at any instant, but by a sequence of rolls and turns it can be brought to any position with any orientation, so no position-level equation is being obeyed.

The practical test is integrability. A Pfaffian form is secretly holonomic if it admits an integrating factor that turns it into \(df = 0\); the Frobenius conditions decide this. If no such factor exists, the constraint is genuinely nonholonomic and cannot be used to eliminate a coordinate. This distinction breaks naive mobility counting: counting configuration-level equations alone overstates the lost freedom when velocity constraints are present, and it changes the solver, since nonholonomic constraints must be carried along as velocity relations (through Lagrange multipliers or quasi-velocities) rather than substituted away.

<svg width="260" height="90" viewBox="0 0 260 90" stroke="currentColor" fill="none" stroke-width="1.5" role="img" aria-label="Rolling disk on a plane"><line x1="10" y1="70" x2="250" y2="70"/><circle cx="70" cy="45" r="25"/><line x1="70" y1="20" x2="70" y2="70"/><path d="M95 45 h40" stroke-dasharray="4 3"/><path d="M128 39 l10 6 l-10 6"/><text x="150" y="49" font-size="10" stroke="none" fill="currentColor">rolling direction only</text></svg>

The consequences reach into control and analysis. Nonholonomic systems can be fully controllable despite having fewer instantaneous velocity directions than configuration coordinates, which is exactly why a car with two velocity inputs can be maneuvered into any parked pose. In modeling terms, a decision about whether contact is treated as ideal rolling (nonholonomic) or as compliant with slip (a force law) determines whether the equations of motion are a differential-algebraic system with velocity constraints or an ordinary differential system with contact forces.
