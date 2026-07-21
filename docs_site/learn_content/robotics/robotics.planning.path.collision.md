**Collision checking** answers the question a planner asks most often: does the robot, placed at a given configuration, intersect any obstacle or itself? It is the oracle underneath sampling-based and graph-search planners alike, and because a planner may issue millions of these queries, collision checking routinely consumes the large majority (often well over 90%) of total planning time. Its efficiency, not the search strategy, is frequently what determines whether a planner runs online.

## Broad phase and narrow phase

Exact geometric intersection tests are expensive, so collision checking is universally organized into two stages. The **broad phase** cheaply rejects pairs that cannot possibly be touching, using conservative **bounding volumes**, axis-aligned boxes (AABBs), oriented boxes (OBBs), spheres, or discrete-orientation polytopes (k-DOPs), organized into a **bounding volume hierarchy (BVH)** or a spatial partition (grid, octree, sweep-and-prune). Only the surviving candidate pairs proceed to the **narrow phase**, which performs the exact test on the underlying geometry. Two convex shapes are disjoint if and only if there exists a **separating axis** onto which their projections do not overlap; equivalently, two convex sets \( A \) and \( B \) intersect if and only if their **Minkowski difference** contains the origin,

\[
A \ominus B = \{\, a - b : a \in A,\; b \in B \,\}, \qquad A \cap B \ne \varnothing \iff \mathbf{0} \in A \ominus B.
\]

The **GJK algorithm** exploits exactly this: it iteratively builds simplices inside the Minkowski difference to decide origin containment and, more usefully, to return the minimum separating distance between two convex bodies, which planners use to reason about clearance rather than mere yes/no contact. Non-convex robot links are handled by decomposing them into convex pieces or bounding them with a convex hull.

## Discrete versus continuous checking

Checking a single static configuration is **discrete** collision detection. But a planner also needs to know whether the *motion* between two configurations is free, and sampling the edge at a finite step size can miss a thin obstacle that the swept body passes through (the classic tunneling failure). **Continuous collision detection (CCD)** closes this gap by treating the edge as a swept motion \( q(s),\ s \in [0,1] \) and either testing the swept volume or advancing conservatively: given the closest distance \( d \) between bodies and a bound on the maximum speed of any point on the moving body, one can advance the motion parameter by a step guaranteed not to cause penetration, and repeat until the whole edge is certified or a contact is found.

## Self-collision and practical structure

A multi-link robot can collide with *itself*, so the same machinery is applied to link-pair tests, with an **adjacency (allowed-collision) filter** that permanently excludes pairs which are always touching or can never reach each other, avoiding wasted work and false positives. Two further ideas dominate real systems. First, distance queries (signed clearance) are preferred over binary tests wherever possible, because clearance feeds cost functions and CCD step sizes. Second, planners use **lazy collision checking**: because the checker is the bottleneck, they defer edge validation until an edge actually appears on a candidate path, checking only what the solution needs rather than the entire roadmap.
