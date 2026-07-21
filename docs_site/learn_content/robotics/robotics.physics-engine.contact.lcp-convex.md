Rigid-body simulators must resolve contact: bodies may touch but must not interpenetrate, contact can only push (never pull), and tangential friction resists sliding up to a limit. These are *unilateral* constraints, and the way an engine formulates and solves them is the single biggest determinant of its speed, stability, and physical fidelity. Two broad families dominate: exact **linear complementarity (LCP)** formulations and relaxed **soft/convex** formulations.

## The complementarity picture

Non-penetration is a Signorini condition. Let \(\phi(q)\) be the signed gap between two bodies and \(\lambda_n \ge 0\) the normal contact impulse. Either the bodies are separated (\(\phi > 0\)) and carry no force (\(\lambda_n = 0\)), or they touch (\(\phi = 0\)) and may carry force. This exclusive-or is a complementarity condition,

\[ 0 \le \phi(q) \;\perp\; \lambda_n \ge 0, \]

meaning both quantities are non-negative and their product is zero. Coulomb friction adds the constraint that the tangential impulse lies inside a cone, \(\lVert \lambda_t \rVert \le \mu\,\lambda_n\), together with a maximum-dissipation principle that aligns sliding friction opposite to relative tangential velocity. Discretized over a timestep with an impulse-velocity (time-stepping) scheme, the normal conditions become a linear complementarity problem, and the friction cone is often approximated by a polyhedral (faceted) cone so the whole system stays an LCP solvable by pivoting or projected iterative methods.

## Why exactness is hard

The attraction of the LCP form is physical correctness: it enforces true non-penetration and a true friction limit. The difficulty is that the coupling of the friction cone to the normal force makes the frictional problem **nonconvex** (a nonlinear complementarity problem), so solutions may fail to exist or be non-unique, and solvers can be slow or brittle in contact-rich scenes with many simultaneous, redundant contacts. Painleve-type paradoxes and inconsistent configurations are real failure modes of the exact model, not just numerical artifacts.

## Soft and convex relaxations

The alternative trades a little physical exactness for a well-posed, fast, and robust solve. **Soft-constraint** models introduce compliance and damping so contact behaves like a stiff spring-damper: penetration is penalized rather than forbidden, and the complementarity is regularized into a smooth problem. Equivalently, one can pose contact resolution as a single **convex optimization** in impulse space,

\[ \min_{\lambda \in \mathcal{K}} \; \tfrac{1}{2}\,\lambda^{\top} (A + R)\,\lambda + \lambda^{\top} b, \]

where \(A\) is the inverse effective-inertia (Delassus) operator in contact coordinates, \(b\) encodes the unconstrained relative velocity, \(\mathcal{K}\) is the (possibly true, second-order) friction cone, and \(R \succeq 0\) is a regularizer that makes the objective strictly convex. Because a convex program always has a solution and is uniquely solvable when \(R \succ 0\), the simulation never gets stuck, and the solve is amenable to fast first-order and Newton methods. The cost is a small, tunable artifact: a bit of interpenetration, some boundary-layer slip, or velocity-dependent friction softening.

## Where the choice matters

Exact LCP-style contact is favored where physical accuracy of stacking, friction limits, and impact is paramount and the scene is modest. Soft/convex contact is favored for real-time control, reinforcement learning, and contact-rich manipulation and locomotion, where robustness, determinism, speed, and (for gradient-based methods) smooth differentiable dynamics outweigh sub-millimeter penetration error. Understanding which regime an engine is in explains its parameters (contact stiffness, solver iterations, regularization, restitution) and its characteristic behaviors under stress.
