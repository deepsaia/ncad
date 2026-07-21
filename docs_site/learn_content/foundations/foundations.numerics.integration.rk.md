Time integration answers a different question from root finding: given an initial value problem
\[
\dot y = f(t, y), \qquad y(t_0) = y_0 ,
\]
advance the state forward in time. **Explicit** methods compute the next state \(y_{n+1}\) purely from quantities already known at or before \(t_n\), so each step is a direct evaluation with no equation to solve. They are the default for smooth, non-stiff dynamics: rigid-body and multibody motion, particle systems, and transient effects where the fastest and slowest phenomena share a comparable time scale.

## From Euler to Runge-Kutta

The simplest explicit method, forward Euler, uses a single slope sample: \(y_{n+1} = y_n + h\, f(t_n, y_n)\). Its local truncation error is \(O(h^2)\) per step and \(O(h)\) globally -- first order, and usually too inaccurate to be economical. **Runge-Kutta** methods raise the order by sampling the slope at several intermediate *stages* within one step and taking a weighted combination. The classical fourth-order method (RK4) is
\[
\begin{aligned}
k_1 &= f(t_n,\, y_n), \\
k_2 &= f\!\left(t_n + \tfrac{h}{2},\; y_n + \tfrac{h}{2}k_1\right), \\
k_3 &= f\!\left(t_n + \tfrac{h}{2},\; y_n + \tfrac{h}{2}k_2\right), \\
k_4 &= f\!\left(t_n + h,\; y_n + h\,k_3\right), \\
y_{n+1} &= y_n + \tfrac{h}{6}\left(k_1 + 2k_2 + 2k_3 + k_4\right),
\end{aligned}
\]
with global error \(O(h^4)\). A general \(s\)-stage explicit scheme is described compactly by its **Butcher tableau** \((A, b, c)\), where \(A\) is strictly lower triangular (so each stage depends only on earlier stages). The tableau entries must satisfy algebraic *order conditions* to achieve a claimed order.

## Adaptive step-size control

A fixed step is wasteful in calm regions and dangerous in sharp ones. **Embedded** Runge-Kutta pairs (Runge-Kutta-Fehlberg, Dormand-Prince) reuse the same stages to produce two estimates of different order; their difference is a cheap local-error estimate. The step is then rescaled toward a target tolerance, roughly \(h_{\text{new}} = h\,(\mathrm{tol}/\mathrm{err})^{1/(p+1)}\), and a step is rejected and retried if the error exceeds tolerance. This makes the integrator take large steps through smooth motion and automatically refine near impacts or rapid transients.

## Stability and the limit of explicit methods

Applying a method to the scalar test equation \(\dot y = \lambda y\) yields \(y_{n+1} = R(h\lambda)\, y_n\); the method is absolutely stable where \(|R(h\lambda)| \le 1\). For every explicit method this **region of absolute stability** is bounded, so \(h\) is capped by the fastest mode \(\lambda\) even when accuracy would permit a much larger step. When a system has components decaying orders of magnitude faster than the dynamics of interest -- a *stiff* system -- this stability limit forces impractically tiny steps, and explicit integration becomes uneconomical. That failure is precisely the motivation for implicit methods.
