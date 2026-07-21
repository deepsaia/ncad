Root finding answers the question \( f(x) = 0 \): given a scalar (or vector) function, locate the argument that drives it to zero. It is the numerical workhorse behind curve/surface intersection, projecting a point onto a parametric curve, evaluating implicit surfaces, and solving the residual equations that appear in constraint and physics solvers. The two design goals -- **fast convergence** and **robustness** (never diverge, never crash) -- are in tension, and mature solvers deliberately blend methods to get both.

## Order of convergence

Let the error at step \(k\) be \(e_k = x_k - x^\*\). A method converges with **order** \(p\) if
\[
\lim_{k\to\infty} \frac{|e_{k+1}|}{|e_k|^{p}} = C < \infty .
\]
Bisection is *linear* (\(p=1\)), halving the error each step regardless of the function. The secant method is *superlinear* (\(p \approx 1.618\), the golden ratio). Newton's method is *quadratic* (\(p=2\)) -- the number of correct digits roughly doubles per step -- but only once you are close enough, and only if \(f'\) is well behaved. High order buys nothing if the iteration walks off to infinity, which is why order alone never decides the algorithm.

## Bracketing: guaranteed but slow

A **bracket** is an interval \([a,b]\) with a sign change, \(f(a)\,f(b) < 0\). For a continuous \(f\) the intermediate value theorem then guarantees a root inside, and bisection can never lose it: each step evaluates the midpoint and keeps the half that still straddles zero. This gives an ironclad, monotone reduction of the interval but only one bit of accuracy per evaluation. Practical solvers such as Brent's method keep a valid bracket at all times while attempting an inverse-quadratic-interpolation or secant step; if the fast step would fall outside the bracket or fails to shrink it enough, they fall back to a bisection step. The result is superlinear speed with the safety net of a guaranteed interval.

## Damping and globalization

Open methods like Newton have no bracket to protect them. The raw step
\[
x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}
\]
can overshoot wildly when \(f'\) is small or the current guess is far from the root. **Damped (globalized) Newton** instead takes \(x_{k+1} = x_k - \lambda_k\, f(x_k)/f'(x_k)\) with a step factor \(\lambda_k \in (0,1]\) chosen so that a merit function such as \(|f|\) actually decreases (an Armijo/backtracking line search). Far from the solution the method behaves like a cautious descent; near it, \(\lambda_k \to 1\) and full quadratic convergence returns. This globalization is what makes Newton-type iterations dependable inside geometry kernels and constraint solvers, where a single divergent step could corrupt an interactive model.

<svg viewBox="0 0 320 120" width="320" height="120" stroke="currentColor" fill="none" stroke-width="1.5"><line x1="20" y1="70" x2="300" y2="70"/><path d="M20 20 C 120 130, 180 10, 300 100"/><line x1="90" y1="64" x2="90" y2="76"/><line x1="230" y1="64" x2="230" y2="76"/><circle cx="160" cy="70" r="3" fill="currentColor"/><text x="84" y="92" font-size="11" stroke="none" fill="currentColor">a</text><text x="226" y="92" font-size="11" stroke="none" fill="currentColor">b</text><text x="150" y="58" font-size="11" stroke="none" fill="currentColor">x*</text></svg>

The practical rule of thumb: **wrap a fast open method inside a guaranteed one.** Bisection or a maintained bracket supplies the convergence guarantee; interpolation or damped Newton supplies the speed. Choosing sensible convergence tolerances (on both the residual \(|f|\) and the step \(|x_{k+1}-x_k|\)), and capping iteration counts, turns a mathematically elegant iteration into an engineering component that fails gracefully rather than hanging.
