Featherstone's spatial-vector notation is a six-dimensional algebra for rigid-body kinematics and dynamics that fuses the angular and linear parts of a motion (or a force) into a single object. Instead of tracking a body's angular velocity and the linear velocity of some reference point as two separate 3-vectors, and likewise carrying a moment and a resultant force separately, spatial notation stacks them into one 6-vector living in a well-defined vector space. The immediate payoff is that the equations of rigid-body dynamics collapse from a thicket of coupled 3-D vector relations into compact 6-D expressions that read almost like the equations for a point mass, which is exactly why the notation underpins the fastest known recursive algorithms for articulated systems.

## Motion and force as dual spaces

The notation is built on Plücker coordinates and keeps a strict distinction between two dual six-dimensional spaces: **motion vectors** (space \(M^6\)) and **force vectors** (space \(F^6\)). A spatial velocity describes the instantaneous motion of a whole rigid body and is written

\[ \hat{v} = \begin{bmatrix} \boldsymbol{\omega} \\ \mathbf{v}_O \end{bmatrix}, \]

where \(\boldsymbol{\omega}\) is the body's angular velocity and \(\mathbf{v}_O\) is the linear velocity of the body-fixed point that instantaneously coincides with the coordinate origin \(O\). A spatial force gathers the net moment \(\mathbf{n}_O\) about \(O\) and the net linear force \(\mathbf{f}\):

\[ \hat{f} = \begin{bmatrix} \mathbf{n}_O \\ \mathbf{f} \end{bmatrix}. \]

Motion and force vectors are dual in the sense that their inner product \(\hat{f}^{\mathsf{T}} \hat{v}\) yields a scalar power. Because they are different spaces they transform under different rules, and conflating them is the classic source of sign and transpose errors that the notation is specifically designed to prevent.

## Spatial cross products, transforms, and inertia

Each space carries its own cross-product operator. For a spatial motion vector \(\hat{v} = (\boldsymbol{\omega}, \mathbf{v}_O)\), the operator acting on other motion vectors is

\[ \hat{v}\times = \begin{bmatrix} \boldsymbol{\omega}\times & \mathbf{0} \\ \mathbf{v}_O\times & \boldsymbol{\omega}\times \end{bmatrix}, \qquad \hat{v}\times^{*} = -\,(\hat{v}\times)^{\mathsf{T}}, \]

where \(\hat{v}\times^{*}\) is the dual operator acting on force vectors and \(\boldsymbol{\omega}\times\) is the ordinary \(3\times 3\) skew-symmetric matrix. These operators generate the velocity-product (Coriolis and centrifugal) terms automatically. Coordinate changes between frames use \(6\times 6\) **Plücker transforms**: a motion vector maps by \({}^{B}X_{A}\), while the matching force transform is the inverse-transpose \({}^{B}X_{A}^{*} = ({}^{A}X_{B})^{\mathsf{T}}\), again reflecting the motion/force duality.

Mass properties enter through the **spatial inertia**, a symmetric positive-definite \(6\times 6\) matrix \(\hat{I}\) that maps a motion vector (velocity) to a force vector (momentum): \(\hat{h} = \hat{I}\,\hat{v}\). It packages the mass \(m\), the first mass moment \(m\mathbf{c}\), and the rotational inertia tensor in one block matrix. With these pieces the equation of motion of a single rigid body becomes the spatial analogue of Newton-Euler,

\[ \hat{f} = \hat{I}\,\hat{a} + \hat{v}\times^{*}\,\hat{I}\,\hat{v}, \]

where \(\hat{a}\) is the **spatial acceleration**, the genuine time derivative of \(\hat{v}\). A subtle but important point is that this spatial acceleration differs from the everyday acceleration of a tracked material point; treating it as the honest derivative of the velocity 6-vector is what keeps the algebra consistent and removes many of the correction terms that plague classical formulations.

## Where it matters

The practical importance of the notation is that it turns the dynamics of a tree of jointed bodies into simple recursions over the connectivity graph. Each joint contributes a motion subspace \(S\) so that the cross-joint velocity difference is \(S\dot{q}\), and quantities propagate outward (velocities, accelerations) and inward (forces) along the tree. This structure yields the Recursive Newton-Euler Algorithm for inverse dynamics in \(O(n)\) time, the Composite Rigid Body Algorithm for the joint-space inertia matrix in \(O(n^2)\), and the Articulated Body Algorithm for forward dynamics in \(O(n)\). These are the workhorses of robot control, multibody simulation, physics engines, and biomechanics, and their derivations are dramatically shorter in spatial notation than in stacked 3-D vectors. The framework is closely related to the screws and twists of classical screw theory, but its explicit motion/force duality and its matrix operators make it especially well suited to systematic, machine-implementable dynamics code.
