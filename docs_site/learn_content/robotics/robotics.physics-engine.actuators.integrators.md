The equations of motion give a body's state derivative, but a computer advances the state in finite steps. An **integrator** is the numerical rule that maps state at time \(t\) to state at \(t + h\), and its choice governs the trade-off every physics engine lives with: larger timesteps and cheaper integrators run faster but risk energy blow-up, drift, and instability. The rigid-body dynamics can be written in the manipulator form \(M(q)\ddot{q} + C(q,\dot{q})\dot{q} + g(q) = \tau\), giving a first-order system in \((q, \dot{q})\) that must be discretized.

## Explicit, semi-implicit, and implicit schemes

Explicit (forward) Euler, \(x_{k+1} = x_k + h\,f(x_k)\), is the simplest but injects energy and goes unstable for stiff systems unless \(h\) is very small. Physics engines overwhelmingly prefer **semi-implicit (symplectic) Euler**, which updates velocity first and then uses the new velocity to update position:

\[ v_{k+1} = v_k + h\,M^{-1} f(x_k, v_k), \qquad x_{k+1} = x_k + h\,v_{k+1}. \]

This costs the same as explicit Euler but is far better behaved: as a symplectic method it does not systematically pump energy into the system, so orbits and oscillators stay bounded. Higher-order explicit methods (e.g., Runge-Kutta 4) give more accuracy per step but cost several force evaluations and are not symplectic. When contacts, stiff springs, or high-gain actuators make the system **stiff**, engines turn to **implicit** or semi-implicit-with-damping schemes that solve a linear system each step; these are stable at large \(h\) at the price of numerical damping and a per-step solve.

## Stiffness and the stability region

Stability is analyzed on the scalar test equation \(\dot{y} = \lambda y\). An explicit method reproduces \(y_{k+1} = R(h\lambda)\,y_k\), and the step is stable only when the *amplification factor* satisfies \(|R(h\lambda)| \le 1\); for explicit Euler this is \(|1 + h\lambda| \le 1\), a small disk that forces tiny steps when \(|\lambda|\) is large. A **stiff** system is one whose eigenvalues span a wide range of magnitudes, so a fast mode (a hard contact, a stiff joint) dictates a step size far smaller than the motion of interest requires. Implicit methods have unbounded (A-stable) stability regions, which is precisely why they are used to keep large timesteps stable, though they trade that stability for artificial energy loss.

## Constraint drift and stabilization

Joints and contacts are constraints \(C(q) = 0\) enforced at the acceleration or velocity level. Numerical error causes the position-level constraint to **drift** (joints slowly pull apart, penetration accumulates). **Baumgarte stabilization** counteracts this by adding restoring terms so the constraint obeys a stable second-order response,

\[ \ddot{C} + 2\alpha\,\dot{C} + \beta^2 C = 0, \]

with \(\alpha, \beta\) chosen to pull the constraint back toward satisfaction each step; projection or post-stabilization steps serve the same purpose. These parameters are why constraints in a simulator behave as slightly soft springs rather than perfectly rigid links.

## Where it matters

The integrator and timestep set the boundary between a simulation that is fast and one that is trustworthy. Too large a step, or an explicit method on a stiff scene, produces jitter, gained energy, exploding stacks, or missed collisions; too small a step wastes computation and can still drift without stabilization. Practically, engineers pick a symplectic base method, choose a timestep short enough to resolve the stiffest retained mode (contact stiffness and actuator gains included), and add implicit terms or constraint stabilization when stiffness would otherwise force impractically small steps. These choices interact directly with the contact solver and actuator models, since those are usually the source of the stiffness in the first place.
