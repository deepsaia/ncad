**Mobility** (also called the *degree of freedom* of a mechanism) is the number of independent input parameters required to fully determine the configuration of every link. It answers the design engineer's first question about any linkage: how many actuators, and how many, does it need to have a definite motion? The classical tool for estimating mobility from topology alone, without solving any geometry, is the **Kutzbach criterion** and its planar simplification, the **Grubler equation**.

The reasoning is a constraint count. Start with \(n\) links, one of which is fixed as ground. Each free link has \(d\) DOF (\(d = 3\) in the plane, \(d = 6\) in space), so the disconnected links carry \(d(n-1)\) freedoms. Every joint \(i\) then removes constraints: a joint that permits \(f_i\) relative freedoms removes \(d - f_i\) of them. Summing over all \(j\) joints gives the general Kutzbach mobility

\[
M = d\,(n - 1) - \sum_{i=1}^{j} (d - f_i) = d\,(n - 1 - j) + \sum_{i=1}^{j} f_i .
\]

For a **planar** mechanism (\(d = 3\)) built entirely from one-DOF lower pairs (revolute and prismatic joints, each \(f_i = 1\)), this collapses to the compact **Grubler equation**

\[
M = 3(n - 1) - 2j .
\]

## A worked example

Consider the ubiquitous planar four-bar linkage: four links (\(n = 4\), including ground) joined by four revolute pairs (\(j = 4\)). Grubler gives \(M = 3(4-1) - 2(4) = 9 - 8 = 1\). One input, say the crank angle, fully determines the pose of every other link, which is exactly why the four-bar is the workhorse of single-degree-of-freedom mechanism design.

<svg viewBox="0 0 260 130" width="260" height="130" stroke="currentColor" fill="none" stroke-width="2">
  <line x1="40" y1="100" x2="210" y2="100" stroke-dasharray="4 4"/>
  <line x1="40" y1="100" x2="70" y2="40"/>
  <line x1="70" y1="40" x2="170" y2="55"/>
  <line x1="170" y1="55" x2="210" y2="100"/>
  <circle cx="40" cy="100" r="5"/>
  <circle cx="210" cy="100" r="5"/>
  <circle cx="70" cy="40" r="5"/>
  <circle cx="170" cy="55" r="5"/>
</svg>

The interpretation of \(M\) is direct. \(M = 1\) is a *constrained mechanism* driven by a single input; \(M = 2\) needs two coordinated inputs (as in many manipulators and differentials); \(M = 0\) is a *statically determinate structure* with no mobility; and \(M < 0\) indicates a *statically indeterminate*, overconstrained assembly. Because the formula counts only links, joints, and joint freedoms, it is fast and topology-driven, but it deliberately ignores the actual dimensions and orientations of the parts. That blind spot is where the criterion can mislead, which is precisely the subject of overconstraint and redundancy: certain special geometries move even when the count predicts they cannot.
