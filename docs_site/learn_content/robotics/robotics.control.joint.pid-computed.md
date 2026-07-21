Joint-space control asks each actuated joint of a manipulator to track a commanded trajectory \( q_d(t) \), the simplest and most widely deployed control layer in robotics. The plant it controls is the rigid-body dynamics of an \(n\)-link arm, which in the manipulator equation takes the form

\[ M(q)\,\ddot q + C(q,\dot q)\,\dot q + g(q) = \tau, \]

where \(M(q)\) is the symmetric positive-definite mass (inertia) matrix, \(C(q,\dot q)\dot q\) collects Coriolis and centrifugal effects, \(g(q)\) is the gravity load, and \(\tau\) is the vector of joint torques. The key difficulty is that this system is nonlinear and heavily coupled: a torque applied at one joint accelerates the others through the off-diagonal terms of \(M\), and the inertia seen at a joint changes with configuration.

## Independent-joint PID

The pragmatic baseline treats each joint as a decoupled single-input system and closes a proportional-integral-derivative loop on the tracking error \(e = q_d - q\):

\[ \tau = K_p\,e + K_i\!\int_0^t e\,d\sigma + K_d\,\dot e. \]

The proportional term supplies a restoring effort proportional to position error (an electronic spring), the derivative term adds damping to suppress overshoot, and the integral term drives steady-state error to zero, notably the constant offset that gravity would otherwise cause. This scheme is robust and easy to tune because gearing and joint friction mask much of the inter-axis coupling, but its performance degrades at high speed, where the neglected \(C\) and \(M(q)\) coupling terms act as disturbances the linear loop must reject rather than anticipate.

## Computed-torque (inverse-dynamics) control

Computed-torque control removes the nonlinearity by feedback linearization: it uses a model of the dynamics to cancel \(M\), \(C\), and \(g\) and impose linear error dynamics of the designer's choosing. Choosing

\[ \tau = M(q)\,\bigl(\ddot q_d + K_d\,\dot e + K_p\,e\bigr) + C(q,\dot q)\,\dot q + g(q) \]

and substituting into the manipulator equation yields the closed-loop error system

\[ \ddot e + K_d\,\dot e + K_p\,e = 0. \]

With diagonal, positive-definite \(K_p\) and \(K_d\), every joint error obeys the same decoupled second-order equation, so the gains map directly to a desired natural frequency \(\omega_n = \sqrt{k_p}\) and damping ratio \(\zeta = k_d/(2\sqrt{k_p})\), independent of configuration or payload. The feedforward part \(M\ddot q_d + C\dot q + g\) supplies the torque the ideal model predicts, while the \(M(K_d\dot e + K_p e)\) term corrects the residual.

Computed torque is exact only to the extent the model is exact; parameter error in link masses, unmodeled friction, and joint flexibility leave residual coupling that must be handled by the linear part or by adaptive/robust augmentation. It is also more computationally and sensor-demanding, requiring the full dynamic model and reliable velocity estimates. In practice controllers span a spectrum: pure PID for slow or highly geared axes, gravity-compensated PD (\(\tau = K_p e + K_d \dot e + g(q)\)) for setpoint regulation with a global stability guarantee, and full computed torque for fast, lightly geared, direct-drive arms where tracking accuracy is dominated by the dynamic coupling.
