Most robot tasks are specified where the work happens, at the tool: move the gripper along a line, hold a wiping force, keep a camera pointed. Operational-space control, introduced by Khatib, formulates the control law directly in the coordinates of the end-effector task \(x\) rather than transforming everything back to joint angles. Its distinguishing feature is that it accounts for the arm's full dynamics as they are felt at the task point, giving a dynamically correct, decoupled response in Cartesian space instead of the configuration-dependent, coupled behavior a naive Jacobian-transpose controller would produce.

## Task-space dynamics

Starting from the joint-space dynamics \(M\ddot q + C\dot q + g = \tau\) and the task kinematics \(\dot x = J(q)\,\dot q\), one projects the equations of motion into task space to obtain

\[ \Lambda(x)\,\ddot x + \mu(x,\dot x) + p(x) = F, \]

where \(F\) is the generalized force applied at the end-effector and

\[ \Lambda(x) = \bigl(J\,M^{-1}J^{T}\bigr)^{-1} \]

is the **operational-space inertia matrix**, the effective mass the environment feels when pushing the tool in each Cartesian direction. The terms \(\mu\) and \(p\) are the Coriolis/centrifugal and gravity terms expressed in task space. Because \(\Lambda\) captures the true directional inertia, using it lets the controller produce identical dynamic response in every direction, unlike the diagonal-mass assumption of independent Cartesian PID.

## The control law and the dynamically consistent inverse

The operational-space control law computes a desired task force with a decoupling model and maps it to joint torques through the Jacobian transpose:

\[ \tau = J^{T}\Bigl[\,\Lambda(x)\bigl(\ddot x_d + K_d\,\dot e + K_p\,e\bigr) + \mu(x,\dot x) + p(x)\Bigr]. \]

After cancellation the task error \(e = x_d - x\) obeys the linear, decoupled system \(\ddot e + K_d \dot e + K_p e = 0\) in Cartesian coordinates, so a straight-line command yields a straight-line motion with uniform stiffness and damping. Force control integrates naturally: a desired contact force is simply added to \(F\) along the constrained directions, unifying motion and force control in one framework.

## Redundancy and null-space behavior

For a redundant arm (more joints than task dimensions) the map from \(F\) to \(\tau\) leaves internal motions free. Operational-space control exploits this with a secondary torque \(\tau_0\) projected into the null space so it cannot disturb the task:

\[ \tau = J^{T}F + \bigl(I - J^{T}\bar J^{T}\bigr)\,\tau_0, \qquad \bar J = M^{-1}J^{T}\Lambda. \]

Here \(\bar J\) is the **dynamically consistent generalized inverse**; using it (rather than the kinematic pseudoinverse) guarantees that the null-space effort accelerates only the internal degrees of freedom and produces no reaction force at the end-effector. This clean separation lets a robot simultaneously perform its primary task while, at strictly lower priority, avoiding joint limits, dodging obstacles, or keeping its posture away from singularities, which is the basis of modern task-priority and whole-body control architectures. The main costs are computational (real-time evaluation of \(M\), \(J\), and \(\Lambda\)) and sensitivity to model error and to kinematic singularities, where \(JM^{-1}J^{T}\) loses rank and \(\Lambda\) blows up, requiring damped or regularized inverses near those configurations.
