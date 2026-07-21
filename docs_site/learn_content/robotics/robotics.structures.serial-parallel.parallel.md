A **parallel manipulator** connects a fixed base to a single moving platform through several independent kinematic chains (**limbs** or legs) acting in parallel. Because load is shared across multiple limbs rather than carried by one serial stack, parallel mechanisms achieve high stiffness, high payload-to-weight ratio, low moving mass (actuators often sit on or near the base), and excellent accuracy, since positioning errors average rather than accumulate. The trade-offs are a comparatively small, awkwardly shaped workspace and more numerous internal singularities.

## Mobility and the two canonical designs

The number of degrees of freedom follows from the Grübler-Kutzbach mobility criterion, which counts constraints removed by the joints of the closed loops:

\[ M = \lambda\,(n - 1 - j) + \sum_{i=1}^{j} f_i, \]

where \(\lambda\) is the motion-space dimension (6 for spatial, 3 for planar), \(n\) the link count, \(j\) the joint count, and \(f_i\) each joint's freedom. The **Stewart-Gough platform** (hexapod) uses six extensible limbs, each in a universal-prismatic-spherical (UPS) arrangement, yielding a full 6-DOF platform; it underpins motion simulators, precision positioners, and machine tools. The **Delta** robot uses three limbs, each driven by a base-mounted rotary or linear actuator and terminating in a spatial parallelogram (four-bar) linkage that constrains the traveling plate to remain parallel to the base, giving 3 purely translational DOF and very high acceleration for light-payload pick-and-place.

## Inverse kinematics is easy; forward kinematics is hard

Parallel mechanisms invert the difficulty profile of serial arms. Given a desired platform pose, the **inverse** problem (solve for each limb's actuated variable) decouples limb by limb and usually has a simple closed form, for example each hexapod leg length is just the distance between its base and platform attachment points:

\[ \ell_i = \lVert\, p + R\,b_i - a_i \,\rVert, \qquad i = 1,\dots,6, \]

with \(a_i\) the base anchors, \(b_i\) the platform anchors, and \((R, p)\) the platform orientation and position. The **forward** problem (find the platform pose from measured actuator values) is a coupled system of polynomial equations with many solutions and generally no closed form, typically solved numerically or by algebraic elimination.

## Singularities and stiffness

Parallel mechanisms exhibit richer singular behavior than serial ones. In addition to *inverse* (workspace-boundary) singularities, they have *direct* (parallel) singularities where the platform gains an uncontrollable instantaneous freedom and can move under zero actuation, causing loss of stiffness and potentially damaging force spikes. Analysis therefore uses two Jacobians relating actuator rates and platform twist, \(J_x\,\dot{x} = J_q\,\dot{q}\); singularities occur when either matrix degenerates. Careful workspace and singularity mapping is essential because usable working volume is confined to a singularity-free region.
