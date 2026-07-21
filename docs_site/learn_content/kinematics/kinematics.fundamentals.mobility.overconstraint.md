The Kutzbach and Grubler formulas count constraints as if every joint removed an *independent* set of freedoms. In reality, the constraints imposed by different joints can be linearly dependent, and when that happens the mobility formula gives the wrong answer. **Overconstraint** is the situation in which the true mobility of a mechanism exceeds the value predicted by the generic count, because special geometry, parallel or intersecting axes, equal link lengths, mirror symmetry, makes some constraint equations redundant.

The rigorous way to see this is to assemble the **loop-closure constraint equations** \(\Phi(\mathbf{q}) = \mathbf{0}\) that every closed kinematic loop must satisfy, then linearize to obtain the **constraint Jacobian** \(J = \partial \Phi / \partial \mathbf{q}\). The instantaneous mobility is the dimension of the null space of \(J\),

\[
M = (\text{total joint freedoms}) - \operatorname{rank}(J),
\]

while the number of **redundant constraints** is the difference between the number of scalar constraint equations and \(\operatorname{rank}(J)\). The Kutzbach criterion implicitly assumes \(J\) has full row rank; whenever geometry makes \(J\) rank-deficient, the formula undercounts mobility by exactly the number of redundant constraints. Some corrected formulations therefore write \(M = d(n-1-j) + \sum f_i + r\), where \(r\) is the number of redundant constraints, a term that can only be found by examining the actual geometry, not the topology.

## Overconstrained mechanisms

The canonical demonstrations are the classical **overconstrained linkages**. The spatial **Bennett 4R linkage** has \(n = 4\), \(j = 4\) revolute joints; Kutzbach in space gives \(M = 6(4-1) - 5(4) = -2\), predicting a rigid structure, yet with Bennett's special ratios of link lengths and twist angles it moves with a full one-DOF cycle. The **Sarrus linkage** produces pure straight-line translation from revolute joints alone, and the **Bricard** and **Goldberg** linkages extend the family. Each is a working proof that geometry, not counting, determines mobility.

## Redundancy and its engineering consequences

Redundancy appears in two distinct guises that are easy to conflate. **Constraint redundancy** (the case above) means more constraints than needed to remove the unwanted freedoms; it makes a mechanism statically indeterminate, so internal loads cannot be found from equilibrium alone and depend on stiffness and manufacturing tolerances. **Kinematic redundancy**, by contrast, is the desirable case in which a manipulator has more actuated joints than the task requires (joint-space dimension \(n\) greater than task-space dimension \(m\)); the extra freedoms are exploited for obstacle avoidance, singularity avoidance, and joint-limit management, using the null space of the task Jacobian.

The practical stakes are high. An overconstrained assembly can be geometrically exact yet **bind, jam, or build up internal stress** the moment real parts deviate from nominal dimensions, because the redundant constraints fight one another. Designers respond by deliberately relaxing constraints (kinematic or exact-constraint design), by exploiting benign overconstraint where the special geometry is manufacturable and adds stiffness, or by adding compliance. Recognizing that the generic mobility count is a *necessary but not sufficient* indicator, and knowing when to trust the rank of the constraint Jacobian instead, is a core competence in mechanism synthesis.
