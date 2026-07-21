A **trajectory** is a path augmented with timing: not merely the geometric sequence of poses a manipulator passes through, but the position, velocity, and acceleration of every actuated variable as an explicit function of time. The first decision in trajectory generation is *which space the trajectory is authored in*. In **joint space**, the designer specifies the time histories of the joint variables directly, \( q(t) = [q_1(t), \dots, q_n(t)]^\top \), and the end-effector motion is whatever the forward kinematics \( X(t) = f(q(t)) \) produce. In **Cartesian space** (task space), the designer specifies the end-effector pose \( X(t) \) (position and orientation), and the required joint motion is recovered at every instant by solving the inverse kinematics \( q(t) = f^{-1}(X(t)) \).

## The kinematic bridge

The two representations are linked by the manipulator Jacobian, which maps joint rates to task-space (twist) rates:

\[
\dot{X} = J(q)\,\dot{q}, \qquad \dot{q} = J(q)^{-1}\dot{X}.
\]

Because \( f \) is nonlinear, a straight line in joint space is generally a curved arc in Cartesian space, and vice versa. This is the crux of the choice. A joint-space trajectory is cheap to compute (no per-sample inverse kinematics), is guaranteed to respect joint velocity and acceleration limits directly, and never leaves the reachable workspace; but the tool-center-point traces an unpredictable curved path that may sweep through unexpected regions. A Cartesian trajectory guarantees the geometrically meaningful behavior a task needs, straight-line moves for insertion or a controlled orientation while tracking a seam, at the cost of solving inverse kinematics (and inverting or pseudo-inverting \( J \)) at every interpolation step.

## Where each dominates, and the failure modes

Cartesian trajectories inherit every pathology of inverse kinematics. Near a **kinematic singularity** \( J \) loses rank, \( J^{-1} \) blows up, and finite Cartesian velocities demand unbounded joint rates. A commanded straight line can also pass outside the workspace, or force a discontinuous jump between inverse-kinematic branches (an elbow flip), even though its endpoints are individually reachable. Joint-space trajectories sidestep all of these because they live natively in the actuated variables, which is why gross point-to-point motions (moving to a pick approach pose, retracting to home) are almost always planned in joint space.

In practice the two are layered: gross transfer moves are executed in joint space for speed and robustness, and process moves that must obey a geometric constraint are executed in Cartesian space with per-sample inverse kinematics. Orientation is handled separately from position in the Cartesian case, typically by interpolating on the rotation group \( SO(3) \) with a screw or quaternion (\(\mathrm{slerp}\)) interpolation rather than interpolating Euler angles component-wise, since naive angle interpolation does not produce constant-rate, well-defined reorientation.
