The **Articulated-Body Algorithm (ABA)** solves the *forward dynamics* problem: given the joint positions \(q\), velocities \(\dot q\), and applied forces/torques \(\tau\), it computes the resulting joint accelerations \(\ddot q\). This is the direction needed for simulation, where the state is integrated forward in time. ABA is remarkable because it does this in \(O(n)\) time for a kinematic tree, avoiding the \(O(n^3)\) cost of forming and inverting the joint-space mass matrix, and it does so without any explicit matrix inversion larger than the per-joint dimension.

## The articulated-body idea

The key concept is the **articulated-body inertia** \(I^{A}_i\) together with a **bias force** \(p^{A}_i\). For an isolated rigid body, applied force and spatial acceleration are related by \(f = I a\). ABA generalizes this to a *sub-tree* that is free to articulate at its internal joints: it finds the effective relationship \(f_i = I^{A}_i a_i + p^{A}_i\) that a body presents to its parent once all of its descendants have been folded in. In other words, each body is replaced by an equivalent inertia that already accounts for how its children will accelerate in response to force. This handle-inertia relationship is what makes the linear-time recursion possible.

## Three sweeps

The algorithm uses three passes over the tree. The **first outward pass** computes each body's spatial velocity \(v_i\) and the velocity-product bias terms, exactly as in the Newton-Euler kinematics recursion. The **inward pass** builds the articulated-body inertias and bias forces from the leaves toward the base; at each joint it computes the quantities that let a child be absorbed into its parent, notably

\[
U_i = I^{A}_i S_i, \qquad D_i = S_i^{\top} U_i, \qquad u_i = \tau_i - S_i^{\top} p^{A}_i,
\]

and then updates the parent's articulated inertia with the projection \(I^{A}_i - U_i D_i^{-1} U_i^{\top}\). Note that \(D_i\) has the dimension of the joint, so the only inversion is trivially small. The **second outward pass** propagates accelerations back down, solving for each joint acceleration

\[
\ddot q_i = D_i^{-1}\bigl(u_i - U_i^{\top} a_{\lambda(i)}\bigr), \qquad a_i = a_{\lambda(i)} + S_i\,\ddot q_i + (\text{bias}) .
\]

## Why it matters

ABA is the standard engine for physics simulation of articulated mechanisms, character animation, and robot dynamics, precisely because its cost scales linearly with the number of bodies while the mass-matrix approach scales cubically. For long chains and branching trees this is a decisive advantage. The trade-off is that ABA gives only \(\ddot q\); when a downstream computation actually needs the mass matrix itself (for operational-space control, constraint solving, or contact resolution), the composite-rigid-body approach is preferred. In practice a solver often keeps both: ABA for pure integration and the mass-matrix route when the matrix is reused.
