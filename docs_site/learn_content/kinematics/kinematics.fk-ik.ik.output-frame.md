Inverse kinematics inverts the forward map: given a desired output frame \(X_d \in SE(3)\), find joint values \(\theta\) such that \(f(\theta) = X_d\). This is what lets an engineer state a task in the space that actually matters (place the tool tip here, at this orientation) and recover the driven inputs that achieve it. Unlike forward kinematics, the problem is nonlinear: a solution is not guaranteed to exist (the target may lie outside the workspace) and, when it does exist, it is generally not unique.

## Solution branches

When solutions exist they usually form a finite, discrete set. Each member is a distinct assembly of the same mechanism that reaches the identical output frame, commonly labelled by physical posture: elbow-up versus elbow-down, wrist-flipped versus not, shoulder-left versus shoulder-right. A general six-revolute serial chain can admit as many as sixteen real inverse solutions. These are the solution branches, and they are separated by singular configurations, so a continuous task path can only stay on one branch unless it passes through a singularity. Robust selection therefore picks the branch closest to the current configuration, respects joint limits, and watches for branch flips that would command a large, discontinuous reconfiguration.

## Closed form versus iteration

Special geometries admit a closed-form (analytic) solution. The classic sufficient condition is Pieper's: when three consecutive revolute axes intersect at a common point (a spherical wrist), the problem decouples into position and orientation subproblems that each solve algebraically. Absent such structure, the standard approach is numerical iteration. Writing the pose error as a spatial twist \(\mathcal{V}\) and using the body Jacobian \(J(\theta)\), a Newton-Raphson step is

\[ \theta_{k+1} = \theta_k + J^{\dagger}(\theta_k)\,\mathcal{V}(\theta_k), \]

where \(J^{\dagger}\) is the Moore-Penrose pseudoinverse. Near singularities the pseudoinverse blows up, so a damped least-squares (Levenberg-Marquardt) variant \(J^{\mathsf T}(JJ^{\mathsf T}+\lambda^2 I)^{-1}\) is used to trade a small tracking error for bounded, stable joint rates.

## Redundancy and self-motion

When the mechanism has more freedoms than the task dimension (more than six for a full spatial pose), inverse kinematics has a continuum of solutions rather than a discrete set. The extra freedom lives in the null space of the Jacobian: joint motions \(\dot\theta \in \ker J\) that leave the output frame fixed. A secondary objective (avoiding joint limits, staying away from singularities, minimizing effort) is projected into that null space, so the mechanism can satisfy the primary pose while optimizing something else. Inverse kinematics of this kind underlies path planning, teaching a mechanism to follow a curve, and any workflow where the output frame, not the joints, is the natural design variable.
