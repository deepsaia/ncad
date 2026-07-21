When the search space is (or can be discretized into) a finite graph, whose vertices are states, edges are feasible transitions, and edge weights are transition costs, the shortest-path problem is solved exactly by classical **graph search**. Robotics reaches for these algorithms whenever the world is naturally a grid or lattice (mobile-robot occupancy maps, state lattices, discretized configuration spaces) or as the query stage sitting on top of a roadmap built by a sampling planner.

## Dijkstra and A\*

**Dijkstra's algorithm** performs a uniform-cost search: it repeatedly expands the unexpanded node with the smallest known cost-from-start \( g(n) \), settling each node with its true minimum cost. For non-negative edge weights it is provably optimal, but it expands outward in every direction equally, doing work proportional to the volume it must sweep before reaching the goal. **A\*** narrows this search by adding a **heuristic** estimate of the remaining cost to the goal, ordering the frontier by

\[
f(n) = g(n) + h(n),
\]

where \( g(n) \) is the cost accrued from the start and \( h(n) \) estimates the cost still to go. Dijkstra is exactly the special case \( h(n) \equiv 0 \). By biasing expansion toward the goal, A\* typically settles far fewer nodes while returning the same optimal path, provided the heuristic satisfies the right conditions.

## Admissibility, consistency, and what they buy

Two properties govern A\*'s guarantees. A heuristic is **admissible** if it never overestimates the true remaining cost, \( h(n) \le h^{*}(n) \); with an admissible heuristic A\* is guaranteed to return an optimal path. A heuristic is **consistent** (monotone) if it obeys the triangle inequality along every edge,

\[
h(n) \le c(n, n') + h(n'), \qquad h(\text{goal}) = 0,
\]

which is the stronger condition: consistency implies admissibility and additionally guarantees that once a node is expanded its cost is final, so no node is ever reopened and the search stays efficient. In a grid, the straight-line (Euclidean) distance to the goal is a canonical admissible-and-consistent heuristic; where diagonal moves are disallowed, Manhattan distance plays the same role. The tighter \( h \) approaches \( h^{*} \), the fewer nodes A\* expands, until at \( h = h^{*} \) it walks straight to the goal.

## Variants for real robots

Static A\* assumes the graph does not change, which robots violate constantly as sensors reveal new obstacles. The **D\*** family (D\*, Focussed D\*, and the simpler **D\* Lite**) supports efficient *incremental replanning*: when an edge cost changes, it repairs only the affected portion of the search rather than replanning from scratch, which is essential for navigation in partially known or dynamic environments. When time is bounded, **weighted A\*** inflates the heuristic by a factor \( \varepsilon > 1 \) to trade a bounded amount of optimality (cost within \( \varepsilon \) of the best) for speed, and **anytime** variants such as ARA\* return a quick feasible path first and then improve it as long as planning time remains.
