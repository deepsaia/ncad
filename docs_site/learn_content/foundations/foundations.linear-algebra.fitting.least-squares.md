**Least-squares fitting** is the standard response to an *overdetermined* problem: more equations than unknowns, so no exact solution exists, and the best one can do is minimize the residual. Given \(A \in \mathbb{R}^{m\times n}\) with \(m > n\), the linear least-squares problem is
\[
\min_{x}\; \|A x - b\|_2^{2}.
\]
The minimizer is characterized by the requirement that the residual \(r = b - Ax\) be orthogonal to the column space of \(A\), which yields the **normal equations**
\[
A^{\top}A\,x = A^{\top}b.
\]
Geometrically, the solution projects \(b\) onto the subspace reachable by \(A\); the fitted values are \(\hat{b} = P b\) with projection matrix \(P = A(A^{\top}A)^{-1}A^{\top}\), and the residual is the part of \(b\) that no combination of columns can explain.

## Solving it well

Although the normal equations are compact, forming \(A^{\top}A\) squares the condition number and can destroy accuracy for ill-conditioned data. The numerically sound approach is to solve through a **QR decomposition** (reducing the problem to \(Rx = Q^{\top}b\)) or, when rank deficiency or near-degeneracy is possible, through the **SVD** and pseudoinverse, which returns the unique minimum-norm solution. When measurements have unequal reliability, a **weighted** least-squares problem \(\min_x \|W^{1/2}(Ax-b)\|_2\) rescales each equation, and when the fit is unstable a **regularized** (Tikhonov / ridge) formulation \(\min_x \|Ax-b\|_2^2 + \lambda\|x\|_2^2\) trades a little bias for a large gain in stability. If both \(A\) and \(b\) carry error, **total least squares** minimizes perpendicular distance and is solved with the SVD rather than the ordinary projection.

## Where it matters

Least squares is the backbone of parameter estimation and geometric fitting in engineering: fitting lines, circles, planes, spheres, and cylinders to measured or scanned points; calibrating sensors and instruments; regression of empirical models; and the linear steps inside registration and alignment pipelines. When the model is nonlinear in its parameters, for example fitting a general conic or reconciling a kinematic chain, the problem is attacked iteratively by linearizing at each step, using **Gauss-Newton** or the more robust **Levenberg-Marquardt** method, each iteration of which is itself a linear least-squares solve. Understanding the linear case, its projection geometry, and its conditioning pitfalls is therefore the prerequisite for the whole family of estimation techniques.
