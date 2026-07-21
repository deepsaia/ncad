This family of methods sits at the heart of fitting and calibration: aligning scans to a model, bundle adjustment, best-fit geometry, and the residual-minimizing engines behind constraint solvers. All three build on the same idea -- approximate the objective locally by a quadratic model, step to that model's minimizer, repeat -- but they differ in how much curvature information they use and how they stay safe.

## Newton's method

For minimizing a smooth scalar \(f(x)\), a second-order Taylor model gives Newton's step
\[
x_{k+1} = x_k - \big[\nabla^2 f(x_k)\big]^{-1}\, \nabla f(x_k).
\]
Near a strict minimum, where the Hessian \(\nabla^2 f\) is positive definite, convergence is **quadratic**. The costs are real: you must form and factorize the Hessian each iteration, and far from the solution the Hessian may be indefinite, so the raw step is not even guaranteed to point downhill. Practical implementations modify the Hessian to be positive definite and add a line search or trust region for global convergence.

## Gauss-Newton for least squares

Many engineering problems are **nonlinear least squares**: minimize \(\tfrac12 \lVert r(x)\rVert^2 = \tfrac12 \sum_i r_i(x)^2\) over a residual vector \(r\). With Jacobian \(J = \partial r/\partial x\), the gradient is \(J^\top r\) and the exact Hessian is
\[
\nabla^2 f = J^\top J + \sum_i r_i\, \nabla^2 r_i .
\]
**Gauss-Newton** simply drops the expensive second term, solving the normal equations \( (J^\top J)\,\Delta x = -J^\top r \). This is excellent when residuals are small or the model is nearly linear, because the discarded term is then negligible -- and it needs only first derivatives. Its weakness is that \(J^\top J\) can be singular or badly conditioned (rank-deficient \(J\)), in which case the step blows up or points nowhere useful.

## Levenberg-Marquardt: damping the step

**Levenberg-Marquardt** cures that fragility by adding a damping term:
\[
\big(J^\top J + \mu I\big)\,\Delta x = -\,J^\top r, \qquad \mu \ge 0 .
\]
When \(\mu\) is large the step approaches a short, safe steepest-descent step; when \(\mu\) is small it recovers the fast Gauss-Newton step. The damping has a clean **trust-region** interpretation: \(\mu\) is the Lagrange multiplier enforcing an implicit bound \(\lVert \Delta x \rVert \le \Delta\) on the step length, so the model is only trusted within a region of controlled size. Implementations adapt \(\mu\) between iterations from the *gain ratio* -- the ratio of actual to predicted reduction in the objective -- shrinking \(\mu\) when the model is accurate and growing it when a step is rejected. A common refinement replaces \(\mu I\) with \(\mu\,\operatorname{diag}(J^\top J)\) so the damping respects each variable's scale.

The progression is a story of curvature versus safety: Newton uses the full Hessian for speed, Gauss-Newton approximates it cheaply for least squares, and Levenberg-Marquardt interpolates between Gauss-Newton and gradient descent to remain robust when the problem is ill-conditioned or the starting guess is poor -- the reason it is the default engine for registration, bundle adjustment, and geometric best-fit.
