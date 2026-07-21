When the index-3 constrained equations of motion are reduced to the index-1 acceleration form and integrated, only the second time derivative of the constraint is enforced directly. The position-level relation \(\Phi(q,t)=0\) and the velocity-level relation \(\dot\Phi=0\) survive only through exact integration, which no numerical method delivers. The result is **constraint drift**: rounding and truncation error accumulate and the solution slowly wanders off the constraint manifold, so joints visibly separate or overlap over a long run. Constraint stabilization is the family of techniques that keep the solution on, or return it to, the manifold.

## Baumgarte stabilization

Baumgarte's idea is to replace the bare acceleration condition \(\ddot\Phi = 0\) with a stable, damped closed-loop equation in the constraint violation,

\[ \ddot\Phi + 2\alpha\,\dot\Phi + \beta^{2}\,\Phi = 0, \qquad \alpha,\ \beta > 0. \]

This is the equation of a damped oscillator in \(\Phi\): any nonzero violation decays toward zero rather than persisting or growing. In practice the acceleration-level right-hand side \(\gamma\) that feeds the saddle-point system is augmented with the feedback terms \(-2\alpha\dot\Phi - \beta^2\Phi\), so no change to the solver structure is needed. The catch is parameter selection: good values of \(\alpha\) and \(\beta\) depend on the integration step size and problem scaling, and there is no universal recipe. Choosing them too large stiffens the system and can force smaller steps; too small and drift is poorly controlled. A common heuristic sets \(\alpha = \beta\) for critical damping, but the method controls drift only asymptotically and never enforces the constraint exactly.

## Projection methods

Projection enforces the constraints to solver tolerance rather than merely damping the error. After an integration step produces a state that has drifted slightly, one projects it back onto the manifold by solving a small constrained least-squares problem: find the minimum-norm correction \(\delta q\) such that \(\Phi(q + \delta q, t) = 0\), which is a Newton iteration on the constraint,

\[ \Phi_q\,\delta q = -\Phi(q,t), \]

repeated to convergence. A companion projection then corrects the velocities so that \(\Phi_q\,\dot q + \Phi_t = 0\) holds. Because projection actively drives the residual below a chosen tolerance, it does not suffer Baumgarte's parameter sensitivity, at the cost of extra linear solves per step.

## Stabilized index-2 formulations

A more structural remedy keeps both the position and velocity constraints in the system at once. The Gear-Gupta-Leimkuhler (GGL) formulation augments the equations with an additional multiplier field that enforces the velocity-level constraint \(\dot\Phi = 0\) alongside the position-level \(\Phi = 0\), yielding a stabilized index-2 DAE whose invariants are both maintained by construction. This avoids the drift of the plain index-1 reduction without relying on tuned feedback gains, and it is well suited to the stiff solvers used for detailed mechanism and contact models. In all three approaches the underlying trade-off is the same: how tightly to hold the manifold versus how much extra computation and stiffness to accept per step.
