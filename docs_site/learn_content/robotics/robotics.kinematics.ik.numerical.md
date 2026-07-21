When a manipulator has no closed-form inverse (an arbitrary link geometry, a redundant chain with more joints than task dimensions, or a whole-body system), inverse kinematics is solved numerically as a root-finding or optimization problem. The idea is to define a pose error between the current end-effector pose \( T(q) \) and the target \( T_d \), then iteratively adjust the joint vector \( q \) to drive that error to zero. Because the error depends nonlinearly on \( q \), the standard approach is Newton-Raphson iteration, which linearizes the forward map around the current guess using the manipulator Jacobian.

## The Newton iteration

Let \( e(q) \) be a 6-vector error (three for orientation, three for position) between \( T(q) \) and \( T_d \); a common choice is the body twist \( \mathcal{V}_b \) such that \( e^{[\mathcal{V}_b]} = T(q)^{-1} T_d \), which correctly handles the \( SO(3) \) part of the error. The Jacobian relates joint-velocity changes to end-effector twist, \( \mathcal{V} = J(q)\,\dot q \), so each Newton step solves the linear system \( J(q)\,\Delta q = e(q) \) and updates

\[ q_{k+1} = q_k + J^{\dagger}(q_k)\, e(q_k), \]

where \( J^{\dagger} \) is the Moore-Penrose pseudoinverse. The iteration repeats until \( \lVert e \rVert \) falls below a tolerance. Near a good initial guess this converges quadratically, which is why numerical IK is fast when seeded well (for example, from the previous control cycle).

The pseudoinverse is what makes the method robust to non-square Jacobians. For a redundant robot (\( n > 6 \)) the system is underdetermined and \( J^{\dagger} \) returns the minimum-norm joint step, leaving a null space \( (I - J^{\dagger}J) \) that can be exploited for secondary objectives such as staying away from joint limits or obstacles. Near a singularity, however, \( J \) loses rank and \( J^{\dagger} \) blows up, commanding enormous joint velocities. The standard remedy is damped least squares (the Levenberg-Marquardt regularization),

\[ \Delta q = J^{\top}\bigl(JJ^{\top} + \lambda^2 I\bigr)^{-1} e, \]

which trades a small steady-state error for bounded, well-behaved joint commands as \( \lambda \) damps the ill-conditioned directions.

Numerical IK is general and extends naturally to constraints, but it carries the burdens of any iterative method: it needs a starting guess and can converge to different branches (or diverge) depending on that seed; it can stall in local minima of the error when the target is unreachable; and each iteration costs a forward-kinematics evaluation plus a Jacobian factorization. In practice the solver is warm-started from the current joint state, capped at a maximum step size and iteration count, and paired with limit-clamping so that the returned configuration is not only pose-accurate but also physically admissible. These same building blocks (Jacobian, pseudoinverse, damping, null-space projection) are what turn a one-shot IK solver into a continuous resolved-rate motion controller.
