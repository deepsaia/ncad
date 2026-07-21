Springs and dampers are the workhorse **force elements** of multibody models. Unlike joints, which remove degrees of freedom, force elements leave the kinematics untouched and instead add a compliant, configuration-dependent force between two bodies. They let a model capture elasticity and energy dissipation without meshing a deformable part: a suspension coil, an engine mount, a rubber bushing, a valve spring, or a first-order approximation of a cable or belt is represented as a scalar force acting along a defined line of action.

## The translational spring-damper-actuator

The standard element connects a point \(P\) on body \(i\) to a point \(Q\) on body \(j\). Let \(\mathbf{d} = \mathbf{r}_Q - \mathbf{r}_P\), the instantaneous length \(l = \lVert\mathbf{d}\rVert\), and the unit line-of-action vector \(\mathbf{u} = \mathbf{d}/l\). The rate of change of length is the relative velocity projected onto the line, \(\dot l = \mathbf{u}^{\mathsf T}(\mathbf{v}_Q - \mathbf{v}_P)\). The scalar force magnitude combines an elastic term, a viscous term, and an optional applied (actuator) term:

\[
f = k\,(l - l_0) + c\,\dot l + f_a(t),
\]

where \(k\) is stiffness, \(l_0\) the free length, and \(c\) the damping coefficient. The force on body \(i\) is \(+f\,\mathbf{u}\) and on body \(j\) is \(-f\,\mathbf{u}\), an equal-and-opposite pair by Newton's third law, and each is turned into generalized forces through its point Jacobian exactly as any applied load is. A rotational spring-damper (RSDA) is the angular analog: a torque \(\tau = k_\theta(\theta - \theta_0) + c_\theta\,\dot\theta\) applied about a relative rotation angle between the two bodies.

## Energy, nonlinearity, and numerics

The spring is conservative and stores potential energy \(U = \tfrac{1}{2}k(l - l_0)^2\); the damper is dissipative and removes power at the rate \(P = c\,\dot l^{2} \ge 0\), which is the mechanism by which a physical damper bounds resonant response. Real elements are frequently **nonlinear**: \(k\) and \(c\) become functions of displacement or velocity, supplied as polynomials or lookup tables (a progressive-rate spring, a digressive shock valve). Because the element is a force law rather than a constraint, arbitrary curves drop in without changing the model's degree-of-freedom count.

<svg viewBox="0 0 240 60" width="240" height="60" stroke="currentColor" fill="none" stroke-width="1.5">
<circle cx="14" cy="30" r="3"/>
<circle cx="226" cy="30" r="3"/>
<path d="M17 18 H70 l6 -8 12 16 12 -16 12 16 12 -16 8 8 H150"/>
<path d="M17 42 H150 M150 34 h30 v16 h-30 z M172 42 H200 M200 30 v24 M226 42 H200"/>
<path d="M150 42 H150 M150 42 V18 M17 30 V18 M17 30 V42"/>
</svg>

Numerically, force elements are gentle to formulate but can be stiff to integrate: a high \(k\) introduces fast oscillatory modes that force explicit integrators to take tiny time steps, so stiff (implicit) integrators are preferred and physical damping improves stability. Care is also needed at the singular case \(l \to 0\), where the line of action \(\mathbf{u}\) is undefined. These elements appear anywhere compliance or damping shapes the dynamics: vehicle suspensions and mounts, machinery isolation, contact-patch approximations, and preload paths where a spring establishes a static operating point before motion begins.
