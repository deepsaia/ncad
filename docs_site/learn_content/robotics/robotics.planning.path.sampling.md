**Sampling-based planning** attacks the motion-planning problem in the robot's **configuration space** \( \mathcal{C} \), the space of all joint configurations, whose free subset \( \mathcal{C}_{\text{free}} \) is the set of configurations that are collision-free. Explicitly building the obstacle region \( \mathcal{C}_{\text{obs}} \) is intractable in high dimensions; a 6- or 7-DOF arm lives in a 6- or 7-dimensional space where the boundary of \( \mathcal{C}_{\text{obs}} \) has no closed form. The key idea is to *never construct* \( \mathcal{C}_{\text{obs}} \). Instead, draw random configurations, keep the ones that are collision-free, and connect nearby free samples with a local planner, using a collision checker as a black-box oracle that answers only "is this configuration (or edge) free?"

## Two archetypes: PRM and RRT

The **Probabilistic Roadmap (PRM)** is a *multi-query* method for static environments. In a preprocessing phase it samples \( N \) configurations, discards those in collision, and connects each to its near neighbors with straight-line local paths that pass the collision check, producing a graph (the roadmap) that captures the connectivity of \( \mathcal{C}_{\text{free}} \). Any subsequent start/goal query is answered by connecting both endpoints to the roadmap and running a graph search. The **Rapidly-exploring Random Tree (RRT)** is a *single-query*, incremental method. It grows a tree rooted at the start: sample a random configuration \( q_{\text{rand}} \), find the nearest tree node \( q_{\text{near}} \), and take a bounded step toward the sample,

\[
q_{\text{new}} = q_{\text{near}} + \eta\,\frac{q_{\text{rand}} - q_{\text{near}}}{\lVert q_{\text{rand}} - q_{\text{near}}\rVert},
\]

adding \( q_{\text{new}} \) if the connecting edge is collision-free. Because a uniformly sampled point is most likely to fall in the largest unexplored Voronoi region, the tree is biased toward rapid exploration of the space. Bidirectional variants (RRT-Connect) grow trees from both the start and the goal and try to join them, which is markedly faster in practice.

<svg viewBox="0 0 220 130" width="220" height="130" stroke="currentColor" fill="none" stroke-width="1.2" aria-label="RRT growing from a root">
  <rect x="5" y="5" width="210" height="120"/>
  <rect x="95" y="20" width="40" height="55"/>
  <circle cx="30" cy="100" r="3" fill="currentColor"/>
  <polyline points="30,100 55,80 80,95 70,60 55,80"/>
  <polyline points="80,95 120,100 160,80 190,55"/>
  <polyline points="120,100 150,110 185,105"/>
  <text x="18" y="115" font-size="9" fill="currentColor" stroke="none">start</text>
</svg>

## Guarantees, optimality, and limits

Sampling-based planners trade completeness for tractability. They are **probabilistically complete**: if a solution exists, the probability of finding it approaches 1 as the number of samples grows without bound. They are *not* complete in finite time, and they cannot certify that no path exists. Standard RRT and PRM also return *feasible* but not *optimal* paths, which are typically jagged and need post-processing (shortcutting, spline smoothing). The **RRT\*** and **PRM\*** variants add a rewiring step so that the solution cost converges to the optimum asymptotically, at higher computational cost.

Two practical realities dominate performance. First, sampling struggles with **narrow passages**: the probability of sampling inside a thin corridor of \( \mathcal{C}_{\text{free}} \) is proportional to its volume, so tight-clearance tasks demand biased or Gaussian sampling strategies. Second, the overwhelming majority of a sampling planner's runtime is spent inside the collision checker, which is why the checker's efficiency (and lazy evaluation strategies that defer checks) largely determines whether a planner is usable online.
