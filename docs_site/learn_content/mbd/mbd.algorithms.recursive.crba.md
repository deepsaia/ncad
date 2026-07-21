The **Composite-Rigid-Body Algorithm (CRBA)** computes the **joint-space inertia matrix** (also called the mass matrix) \(H(q)\) of a kinematic tree. This is the symmetric, positive-definite matrix that appears in the canonical equations of motion

\[
H(q)\,\ddot q + C(q,\dot q)\,\dot q + g(q) = \tau ,
\]

where \(H\ddot q\) is the inertial term, \(C\dot q\) the Coriolis and centrifugal bias, and \(g\) the gravity load. Whereas RNEA can extract \(H\) column by column (at cost \(O(n^2)\) with a large constant), CRBA computes the whole matrix directly and is the most efficient known method for it, running in \(O(n^2)\) with a small constant, and \(O(nd)\) for a tree of depth \(d\).

## Composite inertias

The algorithm's name comes from its central quantity: the **composite rigid-body inertia** \(I^{c}_i\), the spatial inertia of body \(i\) rigidly welded to all of its descendants, computed by summing inward from the leaves:

\[
I^{c}_i = I_i + \sum_{j \in \mu(i)} I^{c}_j .
\]

The insight is that the \((i,j)\) entry of the mass matrix measures how a unit acceleration at joint \(j\) couples into the force felt at joint \(i\). If joint \(j\) is a descendant of joint \(i\), that coupling is exactly the composite inertia of the subtree at \(j\), projected onto the two joints' motion subspaces.

## Assembling the matrix

For a body \(i\), the diagonal block and the off-diagonal couplings to its ancestors \(j\) are

\[
H_{ii} = S_i^{\top} I^{c}_i S_i, \qquad
F = I^{c}_i S_i, \qquad
H_{ij} = F^{\top} S_j = H_{ji}^{\top},
\]

where \(F\) is propagated up the ancestor chain (transformed between frames at each step) and dotted with each ancestor's motion subspace. Only ancestor-descendant pairs interact; joints on separate branches are dynamically decoupled and their off-diagonal entries are structurally zero, which is what gives branched trees their sparsity.

## Why it matters

An explicit mass matrix is needed whenever the dynamics must be reused or reasoned about rather than merely integrated once. CRBA is the standard first step in the \(O(n^3)\) forward-dynamics route (compute \(H\) with CRBA, compute the bias \(C\dot q + g\) with a single RNEA call at \(\ddot q = 0\), then solve the linear system \(H\ddot q = \tau - \text{bias}\) by Cholesky factorization). It also underpins operational-space and task-space control, constraint and contact solvers that need \(H^{-1}\) or its factorization, and analyses of natural frequencies and conditioning. Because \(H\) is symmetric positive-definite, its Cholesky factor is well-conditioned for these downstream solves. For simple integration of long chains the linear-time articulated-body method is faster, but when the matrix itself is the product, CRBA is the right tool.
