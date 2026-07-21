The dynamics of an open-chain robot with \(n\) joints are captured by a single vector equation of motion, most commonly written in the *manipulator form*:

\[
M(q)\,\ddot{q} + C(q,\dot{q})\,\dot{q} + g(q) = \tau
\]

Here \(q\in\mathbb{R}^n\) is the vector of joint positions, \(\dot q\) and \(\ddot q\) are joint velocities and accelerations, and \(\tau\) is the vector of generalized forces (joint torques for revolute joints, forces for prismatic joints). The three configuration-dependent terms on the left each isolate a distinct physical effect, which is exactly why this grouping is preferred over an undifferentiated \(f(q,\dot q,\ddot q)=\tau\): it lets a control law compensate gravity, cancel velocity-coupling, and shape the effective inertia separately.

## The mass matrix M(q)

\(M(q)\) is the \(n\times n\) *joint-space inertia matrix*. It maps joint acceleration to the inertial part of the required torque and generalizes the scalar mass of a point particle. It is always **symmetric and positive definite**, so \(\dot q^\top M(q)\,\dot q = 2\,\mathcal{K}\) is twice the total kinetic energy and is strictly positive for any nonzero motion. Its diagonal entries are the *reflected inertia* seen at each joint; its off-diagonal entries encode inertial coupling, so that accelerating one joint exerts torque on its neighbors. Because \(M\) depends on configuration, the robot feels heavier or lighter depending on how it is folded, which is central to why a naive fixed-gain controller detunes across the workspace.

## The velocity-product term C(q, q̇)̇

\(C(q,\dot q)\,\dot q\) collects the **Coriolis and centrifugal** forces: terms quadratic in velocity that arise because the inertia matrix itself changes as the robot moves. Centrifugal contributions scale with \(\dot q_i^2\) (a single joint's speed), while Coriolis contributions scale with products \(\dot q_i\dot q_j\) of different joint speeds. The matrix \(C\) is not unique, but a canonical *Christoffel-symbol* factorization defines its entries directly from the mass matrix,

\[
c_{ij}(q,\dot q) = \sum_{k=1}^{n}\tfrac{1}{2}\!\left(\frac{\partial M_{ij}}{\partial q_k}+\frac{\partial M_{ik}}{\partial q_j}-\frac{\partial M_{kj}}{\partial q_i}\right)\dot q_k .
\]

This particular choice yields the widely used property that \(\dot M(q)-2C(q,\dot q)\) is **skew-symmetric**, a passivity statement of energy conservation (the internal velocity-product forces do no net work) that many stability proofs and adaptive controllers rely on.

## The gravity term g(q)

\(g(q)=\partial \mathcal{P}/\partial q\) is the gradient of gravitational potential energy \(\mathcal{P}(q)\); it is the static torque each joint must supply merely to hold a pose against gravity, independent of motion. Because it is velocity- and acceleration-free, it is the cheapest term to precompute and the one whose cancellation (*gravity compensation*) most improves practical tracking. Together the three terms follow from the Euler-Lagrange equations applied to \(\mathcal{L}=\mathcal{K}-\mathcal{P}\); when the end-effector also touches the environment, an external-wrench term \(J(q)^\top \mathcal{F}\) is appended, giving \(M\ddot q + C\dot q + g = \tau + J^\top\mathcal{F}\). This structured decomposition is the foundation for computed-torque control, operational-space control, and model-based feedforward, and it is what algorithms such as the recursive Newton-Euler and composite-rigid-body methods evaluate numerically.
