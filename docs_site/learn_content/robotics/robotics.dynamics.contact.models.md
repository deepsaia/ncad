Everything a robot does that matters, walking, grasping, assembly, manipulation, happens through **contact**, and contact is where an otherwise smooth dynamics model becomes nonsmooth. A contact model must answer two coupled questions at each touching point: how large is the **normal force** that prevents interpenetration, and how large is the **friction force** tangent to the surface that resists sliding. Both are set-valued and inequality-constrained, which is what makes contact simulation and contact-rich control fundamentally harder than free-space motion.

## Normal contact: rigid vs. compliant

The idealized *rigid* (hard) model states the **Signorini** condition as a complementarity between gap and force: the separation distance \(\phi\ge 0\), the normal force \(f_n\ge 0\), and they are never both positive at once,

\[
0 \le \phi \;\perp\; f_n \ge 0 ,
\]

meaning contact force acts only when the gap closes. Enforced exactly, this yields a Linear (or Nonlinear) Complementarity Problem each timestep and admits impulsive forces at impact, handled through a coefficient of restitution. The alternative *compliant* (penalty / soft) model replaces the hard constraint with a spring-damper, e.g. \(f_n = \max(0,\; k\,\delta + d\,\dot\delta)\) for penetration depth \(\delta\); it is simple and always solvable but introduces stiff dynamics that force small timesteps and add artificial bounce or sponginess if \(k,d\) are mistuned.

## Tangential contact: the Coulomb friction cone

Dry friction is modeled by **Coulomb's law**: the tangential force magnitude cannot exceed \(\mu\) times the normal force, and while sticking it takes whatever value (up to that bound) enforces zero slip; once sliding, it saturates and opposes the slip velocity \(v_t\):

\[
\lVert f_t\rVert \le \mu f_n,\qquad v_t\neq 0 \;\Rightarrow\; f_t = -\mu f_n\,\frac{v_t}{\lVert v_t\rVert}.
\]

Geometrically the admissible contact wrench lives inside a **friction cone** of half-angle \(\arctan\mu\). Because a circular cone is a second-order (quadratic) constraint, many time-stepping solvers replace it with a **polyhedral (linearized) cone**, trading exact isotropy for a linear-complementarity or linear-programming problem that is fast and robust. This stick-slip switching is the origin of the nonsmoothness: the friction force is a set-valued map at \(v_t = 0\).

## Richer friction and practical trade-offs

Beyond ideal Coulomb, engineering models add **viscous** friction (linear in velocity), the **Stribeck** effect (a dip from higher static/breakaway friction to lower kinetic friction as sliding begins), and dynamic state models such as **LuGre**, which introduces an internal bristle deflection to reproduce pre-sliding displacement, hysteresis, and stiction without the discontinuity at zero velocity. The right choice is a modeling decision, not a universal truth: rigid + exact-cone formulations conserve momentum through impacts and avoid tuning stiffness but require complementarity solvers and can suffer inconsistencies (the classic Painleve paradox); compliant + regularized-friction formulations are trivial to differentiate (useful for gradient-based control and learning) but demand small steps. In all cases the contact wrench enters the equation of motion through the contact Jacobian, \(M\ddot q + C\dot q + g = \tau + \sum_c J_c^\top \mathcal{F}_c\), coupling the choice of contact law directly into the robot's forward dynamics and into any planner that reasons about grasps, footholds, or force control.
