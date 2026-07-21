The slider-crank is the canonical mechanism for converting between rotation and translation, and it is the heart of nearly every reciprocating engine, pump, and compressor. It is kinematically a four-bar linkage in which one revolute joint has been replaced by a prismatic (sliding) joint, equivalent to letting the output rocker grow to infinite length so that its pin travels along a straight guide. The three moving elements are the **crank** of radius \(r\) rotating about a fixed center, the **connecting rod** of length \(l\), and the **slider** (piston) constrained to a line. Like the four-bar it has a single degree of freedom, so one input, the crank angle \(\theta\), fixes the entire configuration.

## Position, velocity, and acceleration

For the in-line slider-crank (slider axis passing through the crank center), the slider position \(x\) measured from the crank center along the axis is obtained from the loop-closure equation \(r\sin\theta = l\sin\phi\), where \(\phi\) is the rod obliquity angle:

\[ x = r\cos\theta + l\cos\phi = r\cos\theta + l\sqrt{1 - \left(\tfrac{r}{l}\right)^2 \sin^2\theta}. \]

Defining the ratio \(\lambda = r/l\) and expanding the square root for the usual case \(\lambda < 1\), the piston displacement from top dead center is approximately

\[ x_{\text{TDC}} \approx r\left[(1-\cos\theta) + \tfrac{\lambda}{4}\,(1-\cos 2\theta)\right]. \]

Differentiating with respect to time for constant crank speed \(\omega\) gives a velocity and, more importantly, an acceleration

\[ \ddot{x} \approx r\omega^2\left(\cos\theta + \lambda\cos 2\theta\right). \]

The \(\cos\theta\) term is the *primary* component and the \(\lambda\cos 2\theta\) term is the *secondary* component that arises purely from the finite rod length. This second harmonic is the source of the secondary shaking force that engine balancing must address, and it is exactly the term that vanishes as \(l \to \infty\).

Because the connecting rod is tilted at angle \(\phi\) whenever the crank is off dead center, the gas or actuation force along the slider produces a transverse *side thrust* reacted by the cylinder wall, and the mechanism has two dead-center positions (top and bottom) where the crank and rod are collinear and the instantaneous mechanical advantage is infinite or zero. An **offset** (eccentric) slider-crank, where the slider axis is displaced from the crank center, introduces a *quick-return* asymmetry: the forward and return strokes occupy unequal crank angles, which is exploited in shapers and other machine tools. The slider-crank matters because it packages the rotation-to-reciprocation conversion into a compact, well-understood loop whose kinematics, force transmission, and inertial imbalance are all captured by the two parameters \(r\) and \(\lambda\).
