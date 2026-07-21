Rigid-body dynamics is posed in two complementary directions, both operating on the same equation of motion \(M(q)\ddot q + C(q,\dot q)\dot q + g(q) = \tau\). **Inverse dynamics** asks: given a desired motion \((q,\dot q,\ddot q)\), what joint torques \(\tau\) produce it? **Forward dynamics** asks the reverse: given the applied torques \(\tau\) and the current state \((q,\dot q)\), what acceleration \(\ddot q\) results? Inverse dynamics is a direct evaluation and is used for control (feedforward torque, computed-torque law) and for actuator sizing. Forward dynamics is an implicit solve for \(\ddot q\) and is the heart of simulation: integrate the resulting acceleration to march the state forward in time.

## Inverse dynamics and the recursive Newton-Euler algorithm

Although one could form \(\tau = M\ddot q + C\dot q + g\) explicitly, the standard is the **Recursive Newton-Euler Algorithm (RNEA)**, which never assembles the matrices. It runs two passes over the kinematic chain. An outward pass, from base to tip, propagates velocities and accelerations link by link:

\[
v_i = v_{i-1} + S_i\dot q_i, \qquad a_i = a_{i-1} + S_i\ddot q_i + \dot S_i \dot q_i,
\]

computing each link's spatial velocity and acceleration and hence its net inertial wrench. An inward pass, from tip to base, sums the wrenches transmitted across each joint and projects them onto the joint axis \(S_i\) to recover \(\tau_i\). The cost is **\(O(n)\)** in the number of joints, dramatically cheaper than building \(M\), \(C\), and \(g\) separately. As a byproduct, RNEA with \(\ddot q = 0\) and \(\dot q = 0\) yields the gravity vector \(g(q)\); with \(\ddot q = 0\) it yields the bias term \(C\dot q + g\).

## Forward dynamics: solving for acceleration

Forward dynamics requires inverting the inertia relationship, \(\ddot q = M(q)^{-1}\bigl(\tau - C(q,\dot q)\dot q - g(q)\bigr)\). A robust route forms \(M\) with the **Composite-Rigid-Body Algorithm (CRBA)** in \(O(n^2)\), obtains the bias \(b = C\dot q + g\) from a single RNEA call with \(\ddot q=0\), and solves the dense linear system \(M\ddot q = \tau - b\) by Cholesky factorization (valid because \(M\) is symmetric positive definite). For long chains the preferred method is Featherstone's **Articulated-Body Algorithm (ABA)**, a three-pass recursion that computes \(\ddot q\) directly in **\(O(n)\)** by propagating *articulated-body inertias* without ever forming or inverting \(M\).

## Why the distinction matters

The two problems have different numerical character and different consumers. Inverse dynamics is well-conditioned, exact, and embarrassingly parallel per-link, making it ideal for real-time torque feedforward at kilohertz control rates. Forward dynamics is an initial-value ODE (or DAE, once constraints and contacts are added) whose accuracy hinges on the integrator and on the conditioning of \(M\), which degrades near kinematic singularities or when mass ratios are extreme. Contacts, closed loops, and joint limits turn the clean \(\ddot q = M^{-1}(\tau - b)\) into a constrained solve (for example a complementarity or KKT system), but the underlying inverse/forward duality and the \(O(n)\) spatial-algebra recursions remain the workhorses of both robot control and physics simulation.
