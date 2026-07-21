The **Recursive Newton-Euler Algorithm (RNEA)** solves the *inverse dynamics* problem for a kinematic tree: given the joint positions \(q\), velocities \(\dot q\), and accelerations \(\ddot q\), it computes the joint forces or torques \(\tau\) required to produce that motion. It is the workhorse behind torque-based control, feedforward compensation, and the assembly of the equations of motion, and it runs in \(O(n)\) time for a chain of \(n\) bodies. Inverse dynamics is the natural direction for control because a controller usually knows the motion it *wants* and needs the actuation that will realize it against gravity, inertia, and Coriolis effects.

## Two recursive sweeps

The algorithm exploits the tree topology with a pair of passes over the bodies. The **outward pass** (from the base toward the leaves) propagates kinematics: each body's spatial velocity and acceleration are built from its parent's by adding the contribution of the connecting joint. Using spatial (6D) vector notation, where a joint of motion subspace \(S_i\) contributes \(\dot q_i\) and \(\ddot q_i\),

\[
v_i = v_{\lambda(i)} + S_i\,\dot q_i, \qquad
a_i = a_{\lambda(i)} + S_i\,\ddot q_i + \dot S_i\,\dot q_i + v_i \times S_i \dot q_i,
\]

where \(\lambda(i)\) is the parent of body \(i\) and the \(\times\) is the spatial cross-product that captures the velocity-dependent (Coriolis and centrifugal) terms.

## From accelerations to forces

Once each body's spatial acceleration is known, the net spatial force on it follows directly from the **Newton-Euler equation** written with the spatial inertia \(I_i\):

\[
f_i^{B} = I_i\,a_i + v_i \times^{*} I_i\,v_i .
\]

The **inward pass** (leaves toward base) then balances forces: the force transmitted across joint \(i\) equals the body's own \(f_i^{B}\) plus everything transmitted up from its children. Projecting that transmitted force onto the joint's motion subspace gives the required generalized force,

\[
f_i = f_i^{B} + \sum_{j \in \mu(i)} f_j, \qquad \tau_i = S_i^{\top} f_i .
\]

Gravity is handled elegantly by initializing the base acceleration to \(-g\) (a fictitious upward acceleration of the whole frame), so gravitational loads fall out of the same recursion without special-casing.

## Why it matters

Because RNEA is exact, linear-time, and free of matrix inversions, it is the standard tool for real-time computed-torque control and gravity compensation. It is also the computational primitive used to *extract* the terms of the equations of motion: calling it with \(\ddot q = 0\) and \(\dot q = 0\) yields the gravity vector \(g(q)\), with \(\ddot q = 0\) it yields the bias force \(C(q,\dot q)\dot q + g(q)\), and calling it repeatedly with unit acceleration vectors reconstructs columns of the mass matrix. This reuse makes it the shared backbone of the forward-dynamics and mass-matrix algorithms as well.
