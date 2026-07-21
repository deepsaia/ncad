## Mapping joint rates to end-effector motion

The kinematic Jacobian is the matrix that relates the rates of a mechanism's joint variables to the resulting velocity of its output frame. If forward kinematics gives the end-effector pose as a function of the joint coordinates, \(\mathbf{x} = \mathbf{f}(\mathbf{q})\), then differentiating with respect to time yields the fundamental first-order relation

\[ \dot{\mathbf{x}} = \mathbf{J}(\mathbf{q})\,\dot{\mathbf{q}}, \qquad \mathbf{J}(\mathbf{q}) = \frac{\partial \mathbf{f}}{\partial \mathbf{q}} . \]

Here \(\dot{\mathbf{q}}\) is the vector of joint velocities and \(\dot{\mathbf{x}}\) is the end-effector twist, its linear and angular velocity stacked together, \(\dot{\mathbf{x}} = [\mathbf{v}^\top\; \boldsymbol{\omega}^\top]^\top\). Crucially \(\mathbf{J}\) is not constant: it depends on the current configuration \(\mathbf{q}\), so the same joint rates produce different tool motions in different poses.

## Building the geometric Jacobian

For a serial chain the Jacobian can be assembled column by column, one column per joint, from the joint axes expressed in the base frame. For a revolute joint \(i\) with axis direction \(\mathbf{z}_{i-1}\) and origin \(\mathbf{o}_{i-1}\), acting on an end-effector at \(\mathbf{o}_n\), the column is

\[ \mathbf{J}_i = \begin{bmatrix} \mathbf{z}_{i-1} \times (\mathbf{o}_n - \mathbf{o}_{i-1}) \\[2pt] \mathbf{z}_{i-1} \end{bmatrix}, \]

while for a prismatic joint, which contributes translation but no rotation,

\[ \mathbf{J}_i = \begin{bmatrix} \mathbf{z}_{i-1} \\[2pt] \mathbf{0} \end{bmatrix}. \]

The top three rows produce the linear velocity contribution and the bottom three the angular. In screw-theory terms each column is simply the joint's screw axis (its twist) expressed in the chosen frame, which is why the same object recurs across position, velocity, and dynamics analysis.

## Inversion, singularities, and duality

Controlling a mechanism usually requires the inverse problem: find the joint rates that achieve a desired tool velocity, \(\dot{\mathbf{q}} = \mathbf{J}^{-1}\dot{\mathbf{x}}\). This inversion fails wherever \(\mathbf{J}\) loses rank, the **kinematic singularities**, detected by \(\det \mathbf{J} = 0\) for a square Jacobian. At a singularity the mechanism instantaneously cannot move its tool in some direction, and the joint rates needed to approach that direction diverge. For a **redundant** manipulator (more joints than task dimensions) \(\mathbf{J}\) is wide and non-invertible; the Moore-Penrose pseudoinverse gives the minimum-norm solution while a nullspace term reconfigures the arm without disturbing the tool,

\[ \dot{\mathbf{q}} = \mathbf{J}^{\dagger}\dot{\mathbf{x}} + (\mathbf{I} - \mathbf{J}^{\dagger}\mathbf{J})\,\dot{\mathbf{q}}_0 . \]

The Jacobian also links forces to torques by a static duality: the joint torques that balance an external wrench \(\boldsymbol{\mathcal{F}}\) on the tool are \(\boldsymbol{\tau} = \mathbf{J}^\top \boldsymbol{\mathcal{F}}\). The same transpose appears in resolved-rate and Jacobian-transpose control schemes.

## Where it matters

Because it captures the full first-order behavior of a mechanism, the Jacobian is central to almost everything downstream: differential (resolved-rate) motion control, numerical inverse kinematics, singularity avoidance in path planning, static force and stiffness analysis, and dexterity measures such as the manipulability index \(w = \sqrt{\det(\mathbf{J}\mathbf{J}^\top)}\) and its associated velocity ellipsoid, which quantify how easily the tool can move or exert force in each direction. It is the workhorse quantity that connects joint space to task space in both robotic manipulators and, through the constraint Jacobian, in closed-loop mechanisms.
