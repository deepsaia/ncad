A *robot description format* is a declarative, text-based specification of a robot's physical structure: its rigid bodies, the joints that connect them, the inertial properties that govern its dynamics, and the geometry used for rendering and collision. Rather than encoding a robot as procedural code inside one tool, these formats capture the model as data that many tools can read: a kinematics library, a motion planner, a dynamics simulator, a visualizer, and controller software can all consume the same file. The three dominant XML dialects are **URDF** (Unified Robot Description Format), **SDF** (Simulation Description Format, sometimes written SDFormat), and **MJCF** (the MuJoCo XML format). They overlap heavily in intent but differ in scope, expressiveness, and the physics assumptions baked into their schemas.

## The kinematic-tree model

All three formats share one core abstraction: a robot is a set of rigid **links** (bodies) connected by **joints**, forming a graph. In URDF that graph must be a strict *tree* — every link has exactly one parent joint except the root — which is why URDF alone cannot natively describe closed-loop mechanisms such as a four-bar linkage or a parallel manipulator. SDF and MJCF relax this by allowing additional constraints or equality relations that close loops. Each joint carries a rigid-body transform from its parent frame to its child frame plus a motion axis, so the pose of a child link is the parent pose composed with a joint transform that is a function of the joint variable \( q \). A single transform is a member of the special Euclidean group \( SE(3) \):

\[ T^{p}_{c}(q) = \begin{bmatrix} R(q) & \mathbf{p}(q) \\ \mathbf{0}^{\top} & 1 \end{bmatrix}, \qquad R \in SO(3),\; \mathbf{p} \in \mathbb{R}^3 . \]

Forward kinematics for a serial chain is then the ordered product of joint transforms from the root, \( T^{0}_{n} = \prod_{i=1}^{n} T^{i-1}_{i}(q_i) \). The standard joint archetypes appear across all three formats: *revolute* (bounded rotation), *continuous* (unbounded rotation), *prismatic* (translation), *fixed* (a rigid weld, useful for attaching sensors or fusing frames), *floating* (six DoF), and *planar* or *ball* variants. The joint *origin* fixes where the axis sits in the parent frame; the joint *axis* is expressed in the child frame. Getting these two conventions right is the single most common source of interchange bugs.

## Dynamics and inertial data

A description meant for simulation, not just visualization, must specify each link's mass, center of mass, and rotational inertia. The inertia of a body about its center of mass is the symmetric \( 3\times 3 \) tensor

\[ I = \begin{bmatrix} I_{xx} & I_{xy} & I_{xz} \\ I_{xy} & I_{yy} & I_{yz} \\ I_{xz} & I_{yz} & I_{zz} \end{bmatrix}, \]

which, together with the joint topology, lets a dynamics engine assemble the equations of motion in generalized coordinates \( q \):

\[ M(q)\,\ddot{q} + C(q,\dot{q})\,\dot{q} + g(q) = \tau, \]

where \( M \) is the mass matrix, \( C \) captures Coriolis and centrifugal terms, \( g \) is gravity loading, and \( \tau \) are the joint torques or forces. Formats also separate *visual* geometry (high-fidelity meshes for rendering) from *collision* geometry (simplified primitives or convex hulls for fast contact queries), because using detailed render meshes for collision is both slow and numerically fragile.

## How the three formats diverge

**URDF** is the most widely authored format and the lingua franca of the ROS ecosystem. It is deliberately minimal: one robot, a strict tree, links with inertial/visual/collision blocks, and joints. It has no notion of the surrounding world, sensors, or physics-engine parameters, and it is usually generated through a macro layer (xacro) that adds parameterization and reuse the base schema lacks. **SDF** was designed to be a self-contained superset for simulation: beyond a single robot it can describe entire worlds, lights, ground planes, multiple interacting models, sensors, actuators, per-engine physics settings, and closed kinematic loops. A URDF file can be converted into SDF almost mechanically, whereas the reverse is lossy because SDF expresses concepts URDF has no place to store. **MJCF** targets a specific high-performance contact-dynamics engine and is optimized for fast, differentiable simulation; it favors body-relative frames, a class-based *defaults* inheritance system to keep files compact, and first-class support for tendons, equality constraints, soft contacts, and actuator models. Its solver-oriented constructs (contact softness, constraint regularization, generalized-coordinate integration choices) often have no clean equivalent in URDF or SDF.

## Why interchange is hard, and where it matters

Because the formats encode not just geometry but *modeling assumptions* — coordinate conventions, whether inertia is given about the link origin or the center of mass, how contacts and joint limits are represented, and which physics parameters exist at all — round-tripping between them is inherently lossy. A model that simulates cleanly in one engine can behave differently in another purely from unstated defaults for friction, damping, or integrator step size. This is a central concern in *sim-to-real* transfer, where a policy trained against a description must survive the gap to hardware, and in *digital twins*, where the same model drives planning, control, and monitoring. In practice, teams treat the robot description as a versioned source-of-truth artifact, validate it by checking that the reconstructed kinematics and mass properties match measured hardware, and document the frame and unit conventions explicitly so that downstream planners, controllers, and simulators all interpret the file the same way.
