A kinematic singularity is a configuration where a mechanism instantaneously loses the ability to move its output in some direction, or equivalently where producing a particular output motion would demand unbounded joint rates. The velocity Jacobian makes this precise. It maps joint rates to the output twist,

\[ \mathcal{V} = J(\theta)\,\dot\theta, \]

and a singularity is any \(\theta\) at which \(J\) drops rank; for a square Jacobian that is exactly the condition \(\det J(\theta) = 0\). At such a pose the image of \(J\) collapses to a subspace, so the set of instantaneously feasible output twists loses a dimension, and the inverse problem becomes ill-conditioned: near the singularity small commanded output motions require very large joint velocities and the transmitted forces spike.

## Where they occur

Singularities split into two families. Boundary singularities sit on the edge of the workspace, where the mechanism is fully extended or fully folded, and they are unavoidable consequences of finite link lengths. Interior singularities occur inside the workspace when axes align, the classic case being a wrist configuration in which two revolute axes become collinear so that two joints produce the same output rotation and one net freedom is lost. Both types matter for control and for planning: a task path that crosses a singularity cannot be tracked at bounded speed and separates the inverse-kinematics solution branches.

## Dead points in single-DOF linkages

The corresponding phenomenon in a single-degree-of-freedom linkage is the dead point (or toggle position). It is a configuration where the chosen input link can no longer drive the output because the transmission angle, the angle at which force is passed from coupler to follower, reaches \(0^{\circ}\) or \(180^{\circ}\). At those poses the mechanical advantage goes to zero or to infinity: the input cannot induce output motion, and the mechanism must be carried through by stored inertia (a flywheel) or a spring. In a four-bar linkage the dead points of the follower occur where the driving crank and coupler become collinear.

<svg viewBox="0 0 240 120" width="240" height="120" stroke="currentColor" fill="none" stroke-width="1.5">
  <line x1="30" y1="100" x2="200" y2="100" stroke-dasharray="4 3"/>
  <line x1="30" y1="100" x2="95" y2="55"/>
  <line x1="95" y1="55" x2="175" y2="55"/>
  <line x1="175" y1="55" x2="200" y2="100"/>
  <circle cx="30" cy="100" r="3" fill="currentColor"/>
  <circle cx="200" cy="100" r="3" fill="currentColor"/>
  <circle cx="95" cy="55" r="3" fill="currentColor"/>
  <circle cx="175" cy="55" r="3" fill="currentColor"/>
  <text x="60" y="40" font-size="9" fill="currentColor" stroke="none">crank + coupler collinear → toggle</text>
</svg>

## Avoid or exploit

Because forces and joint rates degrade near these configurations, motion planning generally keeps a mechanism away from singular poses, and workspace sizing leaves margin from the boundary. Yet the same infinite-mechanical-advantage property is engineered on purpose: over-center toggle mechanisms in clamps, latches, and locking pliers deliberately park at a dead point so that a large external load is held with almost no holding torque, and the joint stays locked until it is driven back over center. Recognizing the singularity and dead-point loci is thus both a safety analysis and a design opportunity.
