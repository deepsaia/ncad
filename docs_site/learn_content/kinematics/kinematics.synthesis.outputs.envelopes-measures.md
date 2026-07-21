Beyond the path of a single point, a designer usually needs to know two things about a mechanism in motion: the region of space its parts occupy over a full cycle, and how selected scalar quantities evolve as the cycle runs. The first is captured by a **motion envelope** (swept region); the second by **measures over time**. Together they answer the packaging, clearance, and performance questions that a static drawing cannot.

## Motion envelopes and swept volumes

As a moving body \( B \) is carried through the motion parameterized by \( t \), the set it occupies is \( B(t) \), and the swept region is the union \( \bigcup_t B(t) \). Its outer skin is the **motion envelope**. If the body's boundary is described implicitly as a moving family of surfaces \( F(\mathbf{x}, t) = 0 \), the envelope is the locus where a surface touches its infinitesimally neighboring position, given by the envelope conditions

\[ F(\mathbf{x}, t) = 0, \qquad \frac{\partial F}{\partial t}(\mathbf{x}, t) = 0. \]

Solving these simultaneously and eliminating \( t \) yields the grazing set that bounds the swept volume; points of \( B(t) \) satisfying only the first equation lie in the interior of the sweep. In practice envelopes are computed either analytically from this condition for simple profiles, or by discretizing the cycle into many poses and taking the union (a Minkowski-style accumulation) of the sampled bodies. The envelope defines the keep-out volume other components must avoid, the guarding a moving assembly requires, and the reachable workspace of a manipulator.

## Measures sampled along the motion

A **measure** is a scalar (or vector) quantity evaluated at every step of the simulated cycle, producing a function of time or of the driving parameter. The common geometric measures are the distance between two points or features, the angle between two links, and the position of a trace point. Differentiating a measure with respect to time gives its rate: for a traced point \( P \),

\[ \mathbf{v}_P = \dot{\mathbf{r}}_P, \qquad \mathbf{a}_P = \ddot{\mathbf{r}}_P, \]

and for a point fixed to a body rotating with angular velocity \( \boldsymbol{\omega} \) and angular acceleration \( \boldsymbol{\alpha} \) about a reference point,

\[ \mathbf{v}_P = \boldsymbol{\omega}\times\mathbf{r}, \qquad \mathbf{a}_P = \boldsymbol{\alpha}\times\mathbf{r} + \boldsymbol{\omega}\times(\boldsymbol{\omega}\times\mathbf{r}), \]

where the last term is the centripetal component. Because closed-form differentiation of a full kinematic chain is tedious, measures are typically obtained numerically: solve the position problem at each sample, then estimate velocity and acceleration by finite differences or by propagating derivatives through the loop-closure Jacobian.

## Why measures drive design decisions

Measures turn a moving picture into verifiable requirements. Peak velocity and acceleration bound the inertial loads and the actuator sizing; a distance or angle measure reveals stroke, dwell, and the closest approach between parts (the *minimum clearance*, which flags interference when it reaches zero). A particularly important linkage measure is the **transmission angle**, the angle between the coupler and the output link, which governs how effectively input force is converted to output force; keeping it away from \(0^{\circ}\) and \(180^{\circ}\) throughout the cycle is a standard quality criterion. By plotting these measures across the full cycle rather than at a single pose, the designer confirms that the mechanism meets its kinematic targets everywhere the machine actually operates, and the swept envelope confirms it does so without collision.
