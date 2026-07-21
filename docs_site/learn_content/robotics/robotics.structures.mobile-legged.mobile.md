A **wheeled mobile robot** achieves locomotion by rolling contact between wheels and ground. Wheels are mechanically simple, energy-efficient on prepared surfaces, and easy to control, which makes them the default for indoor service robots, warehouse vehicles, and planetary rovers on benign terrain. The design problem is choosing a wheel set and arrangement that provides the desired maneuverability while satisfying the rolling constraints, and then relating wheel commands to chassis motion.

## Wheel types and drive configurations

Standard wheels roll in their steering plane and cannot slip sideways; **castor** wheels swivel about an offset axis; **Swedish/Mecanum** wheels add passive rollers on the rim so the contact can slide along one direction; **spherical** wheels are omnidirectional. Common chassis layouts include **differential drive** (two independently driven wheels plus a castor), **Ackermann steering** (car-like, with steered front wheels sharing an instantaneous center), **synchro drive**, and fully **omnidirectional** platforms built from Mecanum or castor wheels. The choice fixes the robot's degree of mobility and steerability, and whether it can translate in any direction or must reorient first.

## Kinematics and the nonholonomic constraint

Most wheeled robots are **nonholonomic**: a standard wheel enforces *rolling without slipping* and *no lateral slip*, which are constraints on velocity that cannot be integrated into constraints on position. A differential-drive robot at pose \((x, y, \theta)\) with forward speed \(v\) and turn rate \(\omega\) obeys

\[ \begin{bmatrix} \dot{x} \\ \dot{y} \\ \dot{\theta} \end{bmatrix} = \begin{bmatrix} \cos\theta & 0 \\ \sin\theta & 0 \\ 0 & 1 \end{bmatrix} \begin{bmatrix} v \\ \omega \end{bmatrix}, \qquad v = \tfrac{r}{2}(\dot{\phi}_R + \dot{\phi}_L), \quad \omega = \tfrac{r}{L}(\dot{\phi}_R - \dot{\phi}_L), \]

with wheel radius \(r\), track width \(L\), and wheel spin rates \(\dot{\phi}_{R,L}\). The lateral constraint \(\dot{x}\sin\theta - \dot{y}\cos\theta = 0\) forbids sideways motion: the robot can reach any pose but not by moving directly sideways, which complicates parking-like maneuvers and motion planning.

## Localization and error

Integrating wheel encoder counts through the kinematic model gives **dead-reckoning odometry**, but wheel slip, unequal radii, and finite encoder resolution make the estimate drift without bound. Practical systems fuse odometry with exteroceptive sensing (laser, vision, inertial, satellite navigation) in a recursive estimator to bound error. The same rolling constraints that simplify control also mean that odometric error grows fastest during turns, where small differences in effective wheel radius produce heading error that then couples into position error.
