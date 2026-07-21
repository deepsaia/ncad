An actuator is the model that turns a control command into the generalized force applied at a joint. The simplest choice, an ideal torque source that instantaneously produces exactly the commanded torque, is convenient but unrealistic. Real actuators have their own dynamics, limits, and losses, and getting these right is central to sim-to-real transfer: a controller tuned against an idealized actuator often fails on hardware whose torque is bandwidth-limited, saturated, geared, and frictional.

## The electromechanical core

Most robots use electric motors, whose torque is proportional to current, \(\tau_m = k_t\, i\), while the electrical side obeys

\[ V = R\,i + L\,\frac{di}{dt} + k_e\,\dot{\theta}_m, \]

where \(R\) and \(L\) are winding resistance and inductance, \(k_e\) is the back-EMF constant, and \(\dot{\theta}_m\) is motor speed. The back-EMF term couples speed to available torque and produces the characteristic falling torque-speed curve. Because the electrical time constant \(L/R\) is usually far shorter than the mechanical one, many simulators drop the inductance and treat the motor as a first-order or even algebraic torque source, but the speed-dependent limit and the current (hence torque) saturation should be kept.

## Gearing and reflected inertia

Most joints place a gearbox of ratio \(G\) between motor and link. Gearing multiplies torque and divides speed, \(\tau_{\text{joint}} = G\,\tau_m\) and \(\dot{\theta}_{\text{joint}} = \dot{\theta}_m / G\), but its most important dynamical effect is that motor and gear inertia appear at the joint scaled by the **square** of the ratio,

\[ I_{\text{reflected}} = G^2\, I_{\text{motor}}. \]

For high-ratio drives this reflected inertia can dominate the link's own inertia, which is why highly geared joints feel stiff and are nearly decoupled from each other, whereas direct-drive joints (\(G \approx 1\)) are backdrivable and strongly coupled. Gearing also introduces friction, backlash, and elasticity that a faithful model may include.

## Beyond the ideal motor

A realistic actuator model adds the losses and limits that shape behavior: viscous and Coulomb (and Stribeck) friction, torque and velocity saturation, and finite bandwidth. Different transmission technologies call for different models entirely: **series-elastic actuators** deliberately insert a compliant element and measure its deflection to sense and control force; **tendon/cable** drives introduce routing and unilateral (pull-only) forces; **pneumatic and hydraulic** actuators have pressure dynamics and are highly nonlinear; and **muscle** models (e.g., Hill-type, with active contractile and passive elastic elements and a force-length-velocity relation) are used in biomechanics. Simulators typically expose these as command modes such as direct torque/force, position, or velocity, where position and velocity modes wrap the actuator in an internal proportional-derivative loop with configurable gains and force limits.

## Where it matters

Actuator modeling determines whether a simulated controller behaves like the real one. Ignoring reflected inertia mis-predicts joint accelerations; ignoring saturation lets a controller command physically impossible torques; ignoring friction and elasticity hides steady-state error and vibration modes. The fidelity should match the purpose: a coarse torque-limit model suffices for gross motion planning, while contact-rich force control, legged locomotion, and learned policies intended for hardware benefit from the electrical, gearing, and friction terms above.
