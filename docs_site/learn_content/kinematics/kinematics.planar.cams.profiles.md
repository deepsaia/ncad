A cam is a shaped member, usually rotating, that imparts a prescribed motion to a **follower** through direct contact. Unlike a linkage, whose output motion is constrained by fixed link lengths, a cam can generate almost any desired follower motion program simply by shaping its profile, which is why cams dominate applications that require precisely timed, arbitrary displacement laws: valve gear, indexing machinery, textile and packaging equipment, and automation cams generally. The design problem separates cleanly into two stages: first choose the *motion program* (the follower displacement as a function of cam angle), then synthesize the *physical profile* that produces it.

## The displacement diagram and its derivatives

The motion program is captured by the **displacement diagram** \(s(\theta)\), the follower lift plotted against cam rotation angle \(\theta\). A full revolution is partitioned into segments, most commonly a **rise**, an upper **dwell** (stationary), a **return**, and a lower dwell. Because the cam turns at angular speed \(\omega = d\theta/dt\), the time derivatives of follower motion follow from the geometric derivatives of \(s(\theta)\) by the chain rule:

\[ v = \frac{ds}{dt} = \omega\,\frac{ds}{d\theta}, \qquad a = \frac{d^2 s}{dt^2} = \omega^2\,\frac{d^2 s}{d\theta^2}, \qquad j = \omega^3\,\frac{d^3 s}{d\theta^3}. \]

Designers therefore study the coupled set of curves \(s\), \(v\), \(a\), \(j\) (displacement, velocity, acceleration, jerk), commonly called the **SVAJ diagrams**. Acceleration is decisive because it multiplies the follower mass to set the inertia force, and jerk governs vibration and shock.

## The fundamental law of cam design

The central rule is that the displacement function must be continuous through at least its **second derivative** across the entire cam cycle. If \(s(\theta)\) has a slope discontinuity, velocity jumps and acceleration becomes an impulse (theoretically infinite); if the acceleration curve has a step, the jerk becomes an impulse and the follower train rings. This immediately rules out naive programs. A **constant-velocity** rise has infinite acceleration at both ends; a **constant-acceleration (parabolic)** rise has finite but discontinuous acceleration (finite jerk spikes); **simple harmonic** motion is smooth in acceleration internally but has an acceleration discontinuity where it meets a dwell.

For rise-dwell-return-dwell cams running at speed, the preferred programs are those whose acceleration goes smoothly to zero at the boundaries. The **cycloidal** motion,

\[ s(\theta) = h\left[\frac{\theta}{\beta} - \frac{1}{2\pi}\sin\!\left(\frac{2\pi\theta}{\beta}\right)\right], \]

where \(h\) is the total lift and \(\beta\) the rise angle, has zero velocity and zero acceleration at both ends, making it join dwells with no acceleration step and giving finite, continuous jerk. Higher-order polynomial programs (the 3-4-5 and 4-5-6-7 polynomials) achieve the same or better continuity and let the designer impose additional boundary conditions. Choosing and blending these segments is the essence of cam profile synthesis, trading peak acceleration, peak velocity, and jerk against one another for the operating speed at hand.
