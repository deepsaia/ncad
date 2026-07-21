Ordinary integrators aim only to keep the local error small. But mechanical systems governed by a Hamiltonian have *structure* -- conserved energy, conserved momenta, and a preserved geometric object called the symplectic form -- and a generic method like RK4 slowly violates all of it. Over a long simulation this shows up as spurious energy drift: an orbit spirals in, a pendulum gains or loses swing, an interactive physics scene visibly gains or bleeds energy. **Geometric (structure-preserving) integrators** are designed to respect these invariants exactly, trading a little local accuracy for correct qualitative behavior over very long times.

## Hamiltonian flow and the symplectic form

For a Hamiltonian \(H(q,p)\) the equations of motion are
\[
\dot q = \frac{\partial H}{\partial p}, \qquad \dot p = -\frac{\partial H}{\partial q}.
\]
The exact flow preserves the **symplectic two-form** \(\omega = \mathrm{d}q \wedge \mathrm{d}p\); geometrically it conserves oriented area in each \((q_i, p_i)\) plane. A numerical map is called **symplectic** when it preserves \(\omega\) too. The canonical example is Störmer-Verlet (leapfrog), for a separable \(H = \tfrac12 p^\top M^{-1} p + V(q)\):
\[
\begin{aligned}
p_{n+1/2} &= p_n - \tfrac{h}{2}\,\nabla V(q_n), \\
q_{n+1} &= q_n + h\,M^{-1} p_{n+1/2}, \\
p_{n+1} &= p_{n+1/2} - \tfrac{h}{2}\,\nabla V(q_{n+1}).
\end{aligned}
\]
It is second order, explicit, symplectic, and time-reversible -- an unusually favorable combination.

## Why energy stays bounded: backward error analysis

Symplectic methods do not conserve the true energy exactly, yet their energy error stays *bounded* rather than drifting. The reason is **backward error analysis**: a symplectic method is (to exponentially high accuracy) the exact flow of a nearby *modified* Hamiltonian \(\tilde H = H + h^r H_r + \cdots\). Since it exactly conserves \(\tilde H\), the true \(H\) merely oscillates within \(O(h^r)\) of its initial value over exponentially long time intervals. This is the precise statement behind the familiar observation that leapfrog "keeps energy stable" where RK4 slowly loses it.

## Variational integrators

A complementary route discretizes the *action* rather than the equations of motion. One replaces the Lagrangian action \(\int L(q,\dot q)\,\mathrm{d}t\) with a **discrete Lagrangian** \(L_d(q_n, q_{n+1})\) approximating the action over one step, then requires the discrete action sum to be stationary. The resulting discrete Euler-Lagrange equations *are* the integrator, and it is automatically symplectic; a discrete Noether theorem makes it conserve momenta associated with symmetries exactly. **Variational integrators** extend cleanly to forced, constrained, and contact-rich systems, which is why they are attractive for constrained multibody and deformable simulation.

Where it matters: long-horizon orbital and molecular dynamics, and any interactive or real-time simulation (cloth, ragdolls, deformables) that must remain energy-stable across thousands of frames. When the goal is faithful long-term qualitative behavior rather than a single accurate trajectory over a short interval, structure preservation beats raw local order.
