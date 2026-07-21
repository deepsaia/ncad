The Unified Robot Description Format is an XML dialect for describing the kinematic and dynamic structure of a robot as a set of rigid **links** connected by **joints**. It originated in the open-source robotics middleware community as a machine-readable, product-neutral way to hand the *same* model to motion planners, physics simulators, visualization tools, and controllers. A file declares each rigid body once and each articulation once, so that forward kinematics, collision geometry, and mass properties all derive from a single source of truth rather than being re-encoded per tool.

The core schema has two element families. A `<link>` carries up to three sub-blocks: `<inertial>` (a mass, a center-of-mass frame, and the six independent entries of the rotational inertia tensor), `<visual>` (a geometry primitive or mesh plus material for rendering), and `<collision>` (usually a coarser geometry used for contact queries). A `<joint>` names a `<parent>` and `<child>` link, a `type` (`revolute`, `continuous`, `prismatic`, `fixed`, `floating`, or `planar`), an `<origin>` giving the fixed pose of the child frame in the parent frame, an `<axis>` of motion, and optional `<limit>`, `<dynamics>` (viscous damping and static friction), `<mimic>`, and `<safety_controller>` blocks. Conventions are fixed and must be respected: SI units (meters, kilograms, radians), a right-handed coordinate system, and orientation given as fixed-axis roll-pitch-yaw so that the rotation matrix is \( R = R_z(\text{yaw})\,R_y(\text{pitch})\,R_x(\text{roll}) \).

## Kinematic tree and forward kinematics

The defining structural constraint is that links and joints form a **tree**, not a general graph: every link has exactly one parent joint except the single root, and cycles are forbidden. This is why the format cannot natively represent a closed-loop or parallel mechanism (a four-bar linkage, a delta arm, a differential) without an auxiliary constraint the format does not carry. The upside of a tree is that the pose of any link follows from a simple product of transforms along the unique path from the root. If \({}^{p}T_{c}(q)\) is the parent-to-child transform of a joint with variable \(q\), it factors into the fixed origin pose and the articulation about the axis,

\[
{}^{p}T_{c}(q) = T_{\text{origin}} \; A(\hat{a}, q),
\]

where \(A\) is a rotation about the joint axis \(\hat{a}\) for a revolute joint or a translation along it for a prismatic joint. The pose of the \(n\)-th link relative to the root is then the ordered composition

\[
{}^{0}T_{n} \;=\; \prod_{i=1}^{n} {}^{i-1}T_{i}(q_i).
\]

## Inertia, geometry, and authoring

The `<inertial>` block specifies the symmetric \(3\times 3\) inertia tensor expressed about the link's center of mass in the inertial frame,

\[
I = \begin{bmatrix} I_{xx} & I_{xy} & I_{xz} \\ I_{xy} & I_{yy} & I_{yz} \\ I_{xz} & I_{yz} & I_{zz} \end{bmatrix},
\]

which, together with mass, feeds the recursive dynamics used by simulators and torque-level controllers. Because the raw XML is verbose and repetitive, models are almost always authored through a macro-expansion preprocessor that adds parameters, loops, and reusable sub-assemblies, then emits flat conforming XML. In practice a well-formed description also demands consistent, decoupled visual and collision meshes and physically plausible inertias; a zero or ill-conditioned inertia tensor is a common source of unstable simulation. The format's deliberate minimalism, a tree of links and joints with SI conventions, is what makes it a durable interchange target, while its silence on environments, sensors, actuators, and loop closure is what motivates the richer formats it is frequently converted into.
