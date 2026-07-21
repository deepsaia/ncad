**Momentum** is the quantity that Newton-Euler dynamics is really about: the equations of motion are most fundamentally statements that force is the time rate of change of linear momentum and moment is the time rate of change of angular momentum. Momentum is useful precisely because it is *conserved* when the corresponding external load vanishes, and because it behaves cleanly across sudden events like impacts, where forces are impulsive and accelerations are ill-defined but momentum change is finite and well behaved.

The **linear momentum** of a body is \(\mathbf{p} = m\,\mathbf{v}_c\), the mass times the velocity of the center of mass. The **angular momentum** about a point \(O\) is the sum \(\mathbf{L}_O = \sum_i \mathbf{r}_i\times m_i\mathbf{v}_i\) over the mass distribution. For a rigid body taken about its own center of mass this collapses to the compact form

\[ \mathbf{L}_c = \mathbf{I}_c\,\boldsymbol{\omega}, \]

which makes explicit that the inertia tensor generally rotates the angular-velocity vector into a non-parallel angular-momentum vector; \(\mathbf{L}_c\) and \(\boldsymbol{\omega}\) are parallel only along a principal axis. Angular momentum about an arbitrary reference point \(O\) decomposes into a spin part and an orbital part, \(\mathbf{L}_O = \mathbf{L}_c + \mathbf{r}_{c/O}\times m\,\mathbf{v}_c\), which is why the choice of reference point must always be stated.

## The balance laws

Newton's and Euler's laws are momentum-rate statements:

\[ \mathbf{F} = \dot{\mathbf{p}}, \qquad \mathbf{M}_c = \dot{\mathbf{L}}_c. \]

When the resultant external force is zero, linear momentum is conserved; when the resultant external moment about a suitable point is zero, angular momentum about that point is conserved. These conservation laws hold for entire multibody systems, not just single parts, because internal joint and contact forces are equal-and-opposite and therefore cancel in the totals. This makes total linear and angular momentum powerful **global invariants** for checking a simulation: in the absence of external loads they should hold constant to within integration tolerance, and any drift signals a modeling or numerical error.

## Impulse and impact

Integrating the balance laws over a time interval gives the **impulse-momentum** relations \(\int \mathbf{F}\,dt = \Delta\mathbf{p}\) and \(\int \mathbf{M}_c\,dt = \Delta\mathbf{L}_c\). During a collision the contact force is large and brief; rather than resolve its detailed profile, impact models work directly with the impulse, applying a coefficient of restitution to the normal relative velocity and a friction law to the tangential component, then solving for the impulse that produces the required post-impact momentum jump. This is how MBD solvers handle contact and impulsive constraints robustly without an unattainably small time step, and why momentum, rather than force, is the currency of collision handling.

## Where it matters

Momentum reasoning underlies reaction-wheel and gyroscopic devices (trading angular momentum between bodies), recoil and thruster analysis, the sizing of clutches and detents that must absorb an impulse, and the validation of long-running dynamic simulations through conserved-quantity monitoring. Because momentum is linear in velocity, it also gives closed-form answers for many blockout and feasibility calculations well before a full force-driven model is built.
