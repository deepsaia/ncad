**Static interference detection** answers a fundamental question about a positioned assembly: at this fixed configuration, do any two solids occupy the same space, and if not, how much clearance separates them? It is *static* because it evaluates a single frozen arrangement of components, as opposed to continuous (dynamic) collision detection, which asks whether two bodies collide anywhere along a swept motion. For a set of \(n\) positioned solids the naive scope is all \(\binom{n}{2}\) ordered pairs, so practical detection is organized to avoid testing pairs that obviously cannot touch.

The relationship between two solids \(A\) and \(B\) falls into three regimes, distinguished by the volume of their intersection and their separation distance. Hard interference (a clash) means the intersection has positive volume, \(\mathrm{vol}(A\cap B) > 0\); contact means they touch with zero-volume overlap; and clearance means they are disjoint with a positive minimum gap,

\[ d(A,B) = \min_{a\in A,\; b\in B} \lVert a - b \rVert > 0. \]

A clearance check compares \(d(A,B)\) against a required threshold so that fasteners, tools, thermal growth, and moving envelopes have room. A useful interference report includes not just a yes/no flag but the interference volume, an estimate of penetration depth, and the offending region, so a designer can act on it.

## Broad phase and narrow phase

Detection is conventionally split into two stages. The **broad phase** cheaply culls pairs that cannot possibly interfere, typically by bounding each solid with an axis-aligned or oriented box and organizing those boxes in a bounding-volume hierarchy or spatial hash; only pairs whose bounds overlap survive. The **narrow phase** then performs the exact or high-fidelity test on each surviving pair. This two-tier structure is what reduces the effective cost well below the quadratic worst case on realistic assemblies where most pairs are far apart.

## Exact versus mesh-based tests

The narrow phase comes in two flavors. An **exact boundary-representation** test operates on the true B-rep: it computes the minimum distance between the surfaces and edges of the two solids, or the boolean intersection to obtain an interference volume, giving results limited only by geometric-kernel tolerance. A **mesh-based** test first tessellates each solid into triangles and then tests triangle-against-triangle overlap, often after decomposing non-convex parts into convex pieces so that convex distance algorithms such as GJK apply. Mesh methods are far faster and scale to very large scenes, at the cost of accuracy bounded by the tessellation chord tolerance, which can miss thin interferences or report false ones near the mesh resolution. The practical choice is exact tests for definitive engineering verification and mesh tests for interactive, whole-assembly scanning.

## Where it matters

Static interference detection is the workhorse of design-for-assembly and design review: confirming that parts physically fit, that mating features align, that maintenance clearances exist, and that no two components share space before anything is manufactured. It also seeds motion studies, whose per-frame checks are just static tests repeated over a sampled trajectory.
