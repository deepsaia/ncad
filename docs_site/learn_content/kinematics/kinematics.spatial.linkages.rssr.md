A **spatial linkage** is a mechanism whose links move through general three-dimensional motion rather than being confined to a single plane or to a set of parallel planes. Where a planar four-bar links four bodies with four revolute (R) joints whose axes are all parallel, a spatial four-bar connects bodies whose joint axes are skew (neither parallel nor intersecting). Joints are named by their kinematic pair: R (revolute, 1 DOF), P (prismatic, 1 DOF), C (cylindrical, 2 DOF), and S (spherical / ball, 3 DOF). The **RSSR** linkage is the canonical spatial four-bar: a driving crank on a fixed revolute axis, a spherical joint to a rigid coupler, a second spherical joint to the output crank, and an output revolute axis fixed to ground. Its purpose is to transmit and coordinate rotation between two skew shafts, something a planar mechanism cannot do.

## Mobility

The usable degrees of freedom of a spatial mechanism follow the spatial Kutzbach–Grübler count, in which each of the \(n\) links has six freedoms in space and each joint \(i\) removes \(6-f_i\) of them:

\[ M = 6\,(n-1-j) + \sum_{i=1}^{j} f_i \]

For the RSSR, \(n=4\) links and \(j=4\) joints with freedoms \(\{1,3,3,1\}\), giving \(M = 6(4-1-4) + (1+3+3+1) = 2\). One of these two freedoms is a **passive** (idle) degree of freedom: the coupler can spin freely about the line joining the two ball centers without affecting the input–output relation. Subtracting that idle rotation leaves an *effective* mobility of one, so a single input crank angle fully determines the mechanism's configuration, exactly as in a planar four-bar. Recognizing and discarding the passive freedom is essential; naive mobility counts otherwise mislabel the linkage as a two-input mechanism.

## Input–output relation

The coupler is a rigid body, so the distance between its two spherical centers \(B\) (carried by the input crank at angle \(\phi\)) and \(C\) (carried by the output crank at angle \(\psi\)) is a constant \(g\). Writing the positions of \(B\) and \(C\) in the fixed frame and imposing \(\lVert \mathbf{r}_C - \mathbf{r}_B \rVert^2 = g^2\) expands to a single scalar constraint that is linear in \(\cos\psi\) and \(\sin\psi\):

\[ A(\phi)\,\cos\psi + B(\phi)\,\sin\psi = C(\phi) \]

where the coefficients depend on the crank lengths, the offset and angle between the fixed axes, and the input angle \(\phi\). This is the spatial analogue of Freudenstein's equation. The half-angle substitution \(t=\tan(\psi/2)\) converts it to a quadratic in \(t\), whose two real roots correspond to the two **assembly configurations** (branches) in which the linkage can be built for a given input. As \(\phi\) advances, the discriminant governs the limits of the crank's range and reveals whether the input is a full crank or an oscillating rocker.

## Why spherical joints, and where it matters

Replacing revolutes with spherical joints is not incidental. A chain of skew revolutes would be **over-constrained**: manufacturing tolerances and small misalignments would bind the mechanism or force it to flex. Each spherical joint contributes three rotational freedoms, absorbing the extra constraints so the RSSR remains an **exact-constraint** (statically determinate) mechanism that assembles and runs without internal stress. This same reasoning drives the use of RSSR and its relatives (RSSP, RCCC, and other spatial four-bars) in steering linkages, independent-suspension geometries, agricultural and off-highway equipment, aircraft control mechanisms, and as spatial function generators that map an input rotation to a prescribed output rotation about a non-parallel axis. Dimensional synthesis of these linkages, whether for function, path, or motion generation, is carried out with loop-closure equations expressed through homogeneous transforms or screw/dual-number algebra.
