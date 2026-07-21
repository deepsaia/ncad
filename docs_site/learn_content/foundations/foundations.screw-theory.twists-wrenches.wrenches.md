A **wrench** is the six-dimensional description of a *system of forces and moments* acting on a rigid body. Just as an arbitrary velocity state needs six numbers, so does an arbitrary loading state: three for the net moment and three for the net force. The wrench is the force-space dual of the twist and is written moment-part-first to match the twist's angular-first ordering,

\[
\mathcal{F} = \begin{bmatrix} m \\ f \end{bmatrix} \in \mathbb{R}^6,
\]

where \(f\) is the resultant force and \(m\) is the resultant moment about the reference frame's origin. The value of \(m\) depends on which point moments are summed about, so a wrench is always stated with respect to a specified frame.

## Poinsot's theorem and the screw

The force-side counterpart of Chasles' theorem is **Poinsot's theorem**: any collection of forces and couples acting on a rigid body reduces to a single resultant force acting along a unique line together with a couple whose axis is parallel to that line, i.e. a force plus a collinear torque, again the bolt-and-nut *screw*. So a wrench, like a twist, is a screw carrying a magnitude, and it possesses the same geometric attributes: a line of action in space and a pitch \(h = m^\top f/\|f\|^2\) relating the collinear moment to the force. A pitch-zero wrench is a pure force through a line; an infinite-pitch wrench is a pure couple.

## Power, duality, and reciprocity

Twists and wrenches live in dual spaces, and their pairing is **power**. The instantaneous work rate done by a wrench on a body moving with a twist is the coordinate-independent scalar

\[
P = \mathcal{F}^\top \mathcal{V} = m^\top \omega + f^\top v.
\]

Because power is invariant, a wrench does not transform like a twist under a change of frame; it transforms by the *transpose-inverse* adjoint, \(\mathcal{F}_a = [\mathrm{Ad}_{T_{ba}}]^\top \mathcal{F}_b\). When \(\mathcal{F}^\top\mathcal{V}=0\) the two screws are said to be **reciprocal**: the wrench does no work through the motion. Reciprocity is the algebraic backbone of constraint analysis: the wrenches a joint or contact can transmit are exactly reciprocal to the twists it permits, and vice versa. This gives a clean way to enumerate the constraint and freedom spaces of a mechanism.

Wrenches are the natural currency of statics and force control. Static equilibrium of a body is \(\sum \mathcal{F} = 0\) as a single 6-vector equation; a manipulator's static joint torques are \(\tau = J^\top \mathcal{F}\), the same Jacobian that maps joint rates to the end-effector twist now mapping the tip wrench back to joint effort; and grasp, contact, and fixture analysis test whether a set of contact wrenches spans (force-closure) or fails to span the space of loads that must be resisted.
