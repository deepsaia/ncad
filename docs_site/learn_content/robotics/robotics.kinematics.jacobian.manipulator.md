The manipulator Jacobian is the linear map that connects joint velocities to end-effector velocity. Where forward kinematics relates positions, \( T = f(q) \), differentiating with respect to time yields the velocity relationship \( \mathcal{V} = J(q)\,\dot q \). Here \( \dot q \) is the vector of joint rates and \( \mathcal{V} \) is the end-effector twist: a 6-vector stacking angular velocity \( \omega \) and linear velocity \( v \). The Jacobian \( J(q) \) is therefore a \( 6 \times n \) matrix that depends on the current configuration \( q \). It is arguably the single most-used object in robot control, because almost everything below the level of trajectory planning is expressed through it.

## Columns are joint screw axes

The Jacobian has a clean geometric interpretation: each column \( J_i \) is the twist that joint \( i \) would generate at the end-effector if it moved at unit rate while all other joints were frozen. For a revolute joint whose axis passes through point \( p_i \) with unit direction \( \hat{z}_i \), the column is

\[ J_i = \begin{bmatrix} \hat{z}_i \\ \hat{z}_i \times (p_e - p_i) \end{bmatrix}, \]

where \( p_e \) is the end-effector origin; a prismatic joint contributes \( J_i = [\,0,\ \hat{z}_i\,]^{\top} \). This makes the Jacobian trivial to assemble column-by-column directly from the forward-kinematics frames, and it matches the screw-theory view exactly: the space Jacobian collects the instantaneous screw axes expressed in the base frame, while the body Jacobian expresses them in the end-effector frame; the two are related by the adjoint transform.

The Jacobian's usefulness comes from being applied in several directions. Forward, \( \mathcal{V} = J\dot q \) predicts end-effector motion from joint motion. Inverted, \( \dot q = J^{\dagger}\mathcal{V} \) is resolved-rate control, the backbone of Cartesian jogging and numerical IK. Transposed, it maps forces to torques through the principle of virtual work,

\[ \tau = J^{\top}(q)\, \mathcal{F}, \]

where \( \mathcal{F} \) is the wrench (force and moment) applied at the tool and \( \tau \) the resulting joint torques. This duality is the basis of static balancing, force control, and impedance control: the same matrix that propagates velocity forward propagates force backward.

Because \( J \) is configuration-dependent, its properties change continuously as the robot moves. Its rank tells you how many independent directions the tool can instantaneously move; its condition number quantifies how evenly it transmits motion and force; and the loss of full rank marks a singularity. For that reason the Jacobian is not merely a control primitive but also the diagnostic lens through which manipulability and singular configurations are analyzed, and its determinant or singular values are monitored in real time on well-behaved systems.
