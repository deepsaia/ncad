**Newton-Raphson iteration** finds a root of a nonlinear equation $f(x) = 0$ by repeatedly
following the function's local tangent to where it crosses zero:

\[
x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}.
\]

In several variables it generalizes with the **Jacobian** $J$ (the matrix of partial derivatives)
in place of the derivative:

\[
x_{k+1} = x_k - J(x_k)^{-1} f(x_k),
\]

solved as the linear system $J\,\Delta x = -f$ each step rather than by forming the inverse.

## Why it is everywhere in CAD/CAE

Newton's method is the numerical core beneath the constraint and kinematics machinery. A sketch
solver drives a residual vector (one entry per constraint) to zero over the sketch's degrees of
freedom; an assembly or mechanism solver does the same over joint variables; a curve/surface
intersection solves $f = 0$ for the parameters where two entities meet. Each is a root-find, and
Newton's **quadratic convergence** near a solution (the error roughly squares each step) is why
these solves feel instantaneous when they are well-posed.

## When it fails, and the safeguards

Newton is fast but not globally safe: a near-singular Jacobian (a redundant or conflicting
constraint set) makes the step blow up, and a poor initial guess can diverge or oscillate. Robust
implementations add **damping** (take a fraction of the full step), **line search** (shorten the
step until the residual actually decreases), and **bracketing** fallbacks for the scalar case. A
singular Jacobian is also diagnostic: its rank deficiency is exactly what a degree-of-freedom
analysis reports as an under- or over-constrained model.
