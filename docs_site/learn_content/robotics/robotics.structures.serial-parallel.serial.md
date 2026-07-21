A **serial manipulator** is an open kinematic chain: a sequence of rigid links connected one after another by actuated joints, running from a fixed base to a free end where a tool or gripper is mounted. Because the chain has exactly one path from base to tip, each joint carries the weight of every link beyond it, and each joint's motion moves the entire downstream chain. The number of independent joints normally equals the number of task degrees of freedom (DOF); six is the classic choice because it is the minimum needed to place the end-effector at an arbitrary position and orientation in three-dimensional space.

The dominant morphologies differ in the *type* and *layout* of their joints. An **articulated** arm uses three or more revolute joints (an RRR shoulder-elbow arrangement) to mimic a human arm, giving a large dexterous reach in a compact footprint. A **SCARA** (Selective Compliance Assembly Robot Arm) places two revolute axes vertically and adds a prismatic vertical axis, so it is stiff against vertical loads but compliant in the horizontal plane, which suits planar pick-and-place and insertion. A **Cartesian** (gantry) robot uses three orthogonal prismatic joints (PPP), trading workspace efficiency for simple, decoupled, highly repeatable straight-line motion. Cylindrical and spherical arms are intermediate mixes of prismatic and revolute axes.

## Forward and inverse kinematics

Each joint contributes a homogeneous transformation relating the coordinate frame of one link to the next. Using the Denavit-Hartenberg convention, the pose of the end-effector frame relative to the base is the ordered product

\[ T_n^0 = A_1(q_1)\,A_2(q_2)\cdots A_n(q_n), \qquad A_i = \begin{bmatrix} R_i & p_i \\ 0 & 1 \end{bmatrix}. \]

This **forward** map from joint values \(q\) to Cartesian pose is unique and cheap to evaluate. The **inverse** problem (find \(q\) achieving a desired pose) is nonlinear and may have zero, multiple, or a continuum of solutions; a six-axis arm with an in-line spherical wrist admits a closed-form solution by kinematic decoupling, whereas general geometries require numerical iteration.

## Velocity, singularities, and workspace

Differentiating the forward map gives the manipulator **Jacobian** \(J(q)\), which maps joint rates to end-effector twist (linear and angular velocity):

\[ \dot{x} = J(q)\,\dot{q}, \qquad \tau = J(q)^{\mathsf T} F. \]

The transpose relation shows the same Jacobian maps an external wrench \(F\) at the tool into joint torques \(\tau\), which is central to force control. Where \(J\) loses rank the arm is at a **singularity**: certain end-effector velocities become unattainable and the required joint rates diverge, so trajectories are planned to avoid these configurations. The set of reachable poses forms the **workspace**, bounded by joint limits and link lengths; the dexterous subset (reachable with full orientation freedom) is smaller than the reachable position envelope. Serial arms are prized for large workspace and flexibility, at the cost of accumulated positioning error and lower stiffness than closed-chain designs.
