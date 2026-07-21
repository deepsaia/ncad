Forward kinematics answers the most basic question in robot geometry: given the joint variables of an open kinematic chain (the angle of each revolute joint, the extension of each prismatic joint), where is the end-effector, and how is it oriented? The answer is a rigid-body pose, conventionally written as a homogeneous transformation \( T \in SE(3) \) that expresses the tool frame in the base frame. Because the map from joint space to task space is a composition of the individual joint motions and the fixed link geometry between them, forward kinematics is always well defined and single-valued: one set of joint values produces exactly one pose. This is the opposite of inverse kinematics, and it is why forward kinematics is the foundation on top of which Jacobians, calibration, and control are all built.

## Denavit-Hartenberg parameters

The classical way to describe the chain is the Denavit-Hartenberg (DH) convention, which attaches a coordinate frame to each link and encodes the geometric relationship between consecutive frames with just four numbers per joint: the link length \( a_i \), the link twist \( \alpha_i \), the link offset \( d_i \), and the joint angle \( \theta_i \). The trick is a canonical placement rule (the joint axis is the \( z \)-axis; the common normal between successive axes is the \( x \)-axis) that collapses what would be six degrees of freedom per transform down to four, because two of the six are absorbed by the frame-placement rule. The transform between link \( i-1 \) and link \( i \) is then a fixed product of two screw motions about \( z \) and \( x \):

\[ T_{i-1,i} = \mathrm{Rot}_z(\theta_i)\, \mathrm{Trans}_z(d_i)\, \mathrm{Trans}_x(a_i)\, \mathrm{Rot}_x(\alpha_i). \]

The full forward map is the ordered product \( T_{0,n} = \prod_{i=1}^{n} T_{i-1,i} \). For a revolute joint the variable is \( \theta_i \); for a prismatic joint it is \( d_i \); the other three parameters are constants baked in by the mechanical design.

## Product of exponentials

The modern alternative is the Product of Exponentials (PoE) formulation, which sidesteps the per-link frame bookkeeping of DH. Every joint is described by a spatial twist (a screw axis) \( \mathcal{S}_i = (\omega_i, v_i) \) expressed in a single fixed base frame, and the motion of that joint is the matrix exponential of the twist scaled by the joint value \( q_i \). Starting from the tool pose at the home configuration \( M \), the forward map in the space frame is

\[ T(q) = e^{[\mathcal{S}_1]q_1}\, e^{[\mathcal{S}_2]q_2}\cdots e^{[\mathcal{S}_n]q_n}\, M, \]

where \( [\mathcal{S}_i] \in \mathfrak{se}(3) \) is the \( 4\times4 \) matrix form of the screw axis. PoE has two practical advantages over DH: it needs no intermediate link frames (only the screw axes and one home pose), and its geometric meaning is transparent, which makes it the natural companion to the twist-based Jacobian. DH remains ubiquitous because tables of four parameters per joint are a compact, standardized way to publish a robot's geometry, but the two descriptions are equivalent and interconvertible.

Forward kinematics is not a one-time calculation; it is evaluated continuously inside the control loop, during trajectory generation, for collision checking of the swept volume, and as the residual in every calibration and inverse-kinematics solver. Small errors in the link parameters propagate directly into end-effector positioning error, which is why kinematic calibration (identifying the true \( a_i, \alpha_i, d_i \) of a physical machine) is a routine step before a chain can hit sub-millimetre accuracy.
