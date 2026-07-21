Optimization is the discipline of choosing the best feasible design: minimize (or maximize) an objective subject to whatever the physics, geometry, or budget requires. It underpins shape and topology optimization, tolerance allocation, path planning, packing and nesting, and constraint-based assembly. Two vocabularies matter -- the **unconstrained** case, which sets up the machinery, and the **constrained** case, which is what most engineering problems actually are.

## Unconstrained optimization

To minimize a smooth \(f: \mathbb{R}^n \to \mathbb{R}\), the **first-order necessary condition** is stationarity, \(\nabla f(x^\*) = 0\). A **second-order sufficient condition** for a strict local minimum adds positive-definite curvature, \(\nabla^2 f(x^\*) \succ 0\). Algorithms iterate along descent directions \(p_k\) (steepest descent, Newton, or quasi-Newton such as BFGS, which builds curvature from gradient differences) and enforce sufficient decrease with a **line search** (Armijo/Wolfe conditions) or a **trust region** to guarantee global convergence from a poor start. **Convexity** is the great dividing line: if \(f\) is convex, any local minimum is global and the stationarity condition is not just necessary but sufficient, which is why so much effort goes into recognizing or reformulating problems as convex.

## Constrained optimization and the KKT conditions

The general problem adds inequality and equality constraints:
\[
\min_x \; f(x) \quad \text{s.t.}\quad g_i(x) \le 0,\; h_j(x) = 0 .
\]
Form the **Lagrangian** \(\mathcal{L}(x,\lambda,\nu) = f(x) + \sum_i \lambda_i\, g_i(x) + \sum_j \nu_j\, h_j(x)\). Under a constraint qualification, any local minimum \(x^\*\) satisfies the **Karush-Kuhn-Tucker (KKT) conditions**:
\[
\begin{aligned}
&\nabla f(x^\*) + \sum_i \lambda_i \nabla g_i(x^\*) + \sum_j \nu_j \nabla h_j(x^\*) = 0 &&\text{(stationarity)}\\
&g_i(x^\*) \le 0,\quad h_j(x^\*) = 0 &&\text{(primal feasibility)}\\
&\lambda_i \ge 0 &&\text{(dual feasibility)}\\
&\lambda_i\, g_i(x^\*) = 0 &&\text{(complementary slackness)}
\end{aligned}
\]
Complementary slackness encodes the intuition that a constraint either binds (\(g_i = 0\), with a nonnegative price \(\lambda_i\)) or is inactive (\(g_i < 0\), with \(\lambda_i = 0\)). For convex problems the KKT conditions are also **sufficient** for global optimality. The multipliers double as **shadow prices**: \(\lambda_i\) measures how much the optimum improves per unit relaxation of constraint \(i\) -- directly useful sensitivity information for design.

## Methods and duality

Solving constrained problems means handling the constraints numerically. **Penalty** and **augmented Lagrangian** methods fold constraints into the objective with growing weights; **sequential quadratic programming (SQP)** solves a quadratic model with linearized constraints at each step, effectively applying Newton's method to the KKT system; **interior-point (barrier)** methods approach the solution from strictly inside the feasible region and are the workhorse for large convex programs. Underlying all of it is **Lagrangian duality**: the dual function \(q(\lambda,\nu) = \inf_x \mathcal{L}\) gives a lower bound on the optimum (weak duality), and under a regularity condition such as Slater's the bound is tight (strong duality), which is what makes dual and interior-point methods provably accurate. In engineering practice the recurring skill is *modeling*: casting a design goal as objective plus constraints, recognizing convex structure where it exists, and reading the multipliers as the price of each requirement.
