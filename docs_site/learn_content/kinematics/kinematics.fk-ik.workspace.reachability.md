The workspace of a mechanism is the set of poses its output frame can attain, and it is the geometric answer to "what can this thing actually reach?" Two nested definitions are standard. The reachable workspace is the set of positions the output-frame origin can occupy in at least one orientation for some admissible configuration. The dexterous workspace is the subset of those positions reachable in every orientation. By construction the dexterous workspace is contained in the reachable workspace, and for many designs it is dramatically smaller or even empty.

## What sets the boundary

Workspace extent is fixed by link dimensions and joint travel limits. The canonical illustration is a planar two-revolute arm with link lengths \(l_1\) and \(l_2\) and unlimited joints: its reachable workspace is the annulus with outer radius \(l_1 + l_2\) (both links extended) and inner radius \(|l_1 - l_2|\) (the second link folded back). Adding joint limits carves the annulus into a partial sector, and interference between links removes further regions.

<svg viewBox="0 0 220 180" width="220" height="180" stroke="currentColor" fill="none" stroke-width="1.5">
  <circle cx="70" cy="90" r="75"/>
  <circle cx="70" cy="90" r="25" stroke-dasharray="4 3"/>
  <line x1="70" y1="90" x2="118" y2="55"/>
  <line x1="118" y1="55" x2="140" y2="110"/>
  <circle cx="70" cy="90" r="3" fill="currentColor"/>
  <circle cx="118" cy="55" r="3" fill="currentColor"/>
  <circle cx="140" cy="110" r="3" fill="currentColor"/>
  <text x="150" y="20" font-size="10" fill="currentColor" stroke="none">r = l₁+l₂</text>
  <text x="20" y="90" font-size="10" fill="currentColor" stroke="none">|l₁-l₂|</text>
</svg>

## Computing and reading it

For open chains the outer boundary is a purely geometric envelope, but general workspaces are found by sampling: evaluate forward kinematics over a dense or randomized set of joint values and collect the reachable poses (a Monte Carlo cloud), or trace the boundary analytically where the geometry permits. A key structural fact is that the boundary of the reachable workspace consists of singular configurations, the postures where the mechanism is fully extended or fully folded and instantaneously loses a degree of output motion. This ties reachability directly to the singularity analysis of the next topic.

Closed-loop and parallel mechanisms behave differently: their workspaces are typically compact and irregular, bounded not by simple link-length envelopes but by loci where the mechanism would pass through a singularity or where links would collide, and they can contain interior holes. Reachability analysis therefore does real design work, confirming that a required task region is fully covered, that it lies inside the dexterous subset when arbitrary orientation is needed, sizing links to place a target comfortably away from the boundary, and positioning the mechanism relative to the part it operates on.
