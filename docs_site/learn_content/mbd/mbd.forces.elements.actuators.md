An actuator is the element through which a multibody model injects controlled effort into a mechanism: a motor turning a joint, a hydraulic cylinder extending a linkage, a linear drive positioning a stage. Conceptually there are two ways to model one, and the choice determines what the solver is asked to compute. A **force-driven** actuator prescribes the force or torque and lets the resulting motion emerge from the dynamics (forward dynamics). A **motion-driven** actuator prescribes the motion and lets the solver report the effort required to produce it (inverse dynamics). Both are legitimate; they answer different engineering questions.

## Force-driven actuation

A force actuator simply contributes a known effort to the generalized applied-force vector. Expressed in joint space, the equations of motion read

\[
\mathbf{M}(\mathbf{q})\,\ddot{\mathbf{q}} + \mathbf{c}(\mathbf{q},\dot{\mathbf{q}}) = \boldsymbol{\tau},
\]

where \(\mathbf{c}\) collects Coriolis, centrifugal, gravity, and other applied terms, and \(\boldsymbol{\tau}\) is the actuator torque/force acting on the corresponding degrees of freedom. The effort may be an open-loop time history \(\boldsymbol{\tau}(t)\) or the output of a feedback controller. A common closed-loop law is proportional-integral-derivative control,

\[
\tau = K_p\,e + K_i\!\int_0^t e\,\mathrm{d}t + K_d\,\dot e, \qquad e = q_{\mathrm{ref}} - q,
\]

which drives a coordinate toward a reference while the mechanism's own inertia and any disturbance loads oppose it. This is the natural form for co-simulation with a control system and for studying how a real drive, with finite gains and bandwidth, tracks a target.

## Motion-driven actuation and effort recovery

When the trajectory is known and the goal is to size the drive, the actuator is modeled as a **driving (rheonomic) constraint** that appends a prescribed-motion equation to the constraint set, for example

\[
\Phi^{\mathrm d}(\mathbf{q},t) = q_i - f(t) = 0,
\]

so the coordinate follows the specified function \(f(t)\) exactly. The actuation effort needed to enforce this appears as the associated Lagrange multiplier: the reaction term \(\boldsymbol{\Phi}_{\mathbf q}^{\mathsf T}\boldsymbol{\lambda}\) in the equations of motion contains the force or torque the actuator must deliver. Extracting that multiplier is precisely how peak torque, power, and duty cycle are read off for motor and cylinder selection, without ever guessing a gain set.

The two views are complementary and are often used in sequence: a motion-driven pass sizes the actuator and reveals the required effort envelope, then a force-driven pass with a realistic controller checks whether an actual drive can track the motion under load. Actuators matter across robotics (joint motors and their reflected inertia), production machinery (cams reproduced as prescribed motions), hydraulics and pneumatics, and any mechatronic system where the plant dynamics and the control loop must be evaluated together. Practical fidelity comes from including actuator limits (force/torque saturation, velocity limits) and, when relevant, drivetrain compliance and reflected inertia, since these dominate real bandwidth.
