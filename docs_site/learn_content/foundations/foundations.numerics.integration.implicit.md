A system is **stiff** when it contains dynamics on widely separated time scales -- fast modes that decay almost instantly alongside slow modes that carry the behavior of interest. For such systems the step size of an explicit method is limited not by accuracy but by *stability*: the fast, already-negligible modes force impractically small steps. Implicit methods exist to break that link, letting the step size be governed by accuracy alone.

## The implicit idea

An implicit method evaluates the right-hand side at the *unknown* new state. Backward (implicit) Euler is the prototype:
\[
y_{n+1} = y_n + h\, f(t_{n+1},\, y_{n+1}).
\]
Because \(y_{n+1}\) appears on both sides, each step requires solving a (generally nonlinear) algebraic system, usually by a Newton iteration that repeatedly forms and factorizes the Jacobian \(\partial f/\partial y\). The payoff is stability. On the test equation \(\dot y = \lambda y\) backward Euler gives \(R(z) = 1/(1-z)\) with \(z = h\lambda\), and \(|R(z)| \le 1\) for the entire left half-plane \(\operatorname{Re}(z) \le 0\). Such a method is **A-stable**: no stability restriction on \(h\) for any decaying mode. Backward Euler is also **L-stable** (\(R(z)\to 0\) as \(z\to-\infty\)), so it strongly damps the stiffest modes rather than letting them ring.

## Common families

The **trapezoidal rule**, \(y_{n+1} = y_n + \tfrac{h}{2}\big(f_n + f_{n+1}\big)\), is A-stable and second order but not L-stable, so it can leave lightly damped oscillations on very stiff modes. **Backward differentiation formulas (BDF)** approximate the derivative from several past solution values,
\[
\sum_{j=0}^{k} \alpha_j\, y_{n+1-j} = h\,\beta_0\, f(t_{n+1}, y_{n+1}),
\]
and are the standard multistep choice for stiff problems up to order 6 (orders 1 and 2 are A-stable; higher orders trade a little stability for accuracy). **Implicit Runge-Kutta** schemes such as the Radau family combine high order with strong stability at the cost of larger stage systems.

## Cost, trade-offs, and where it matters

Every implicit step is expensive: it needs the Jacobian and a linear solve (or several, within Newton). The bet is that far larger stable steps more than repay that per-step cost on a stiff problem, whereas on a non-stiff problem an explicit method wins outright. Implicit integrators are also the natural home for **differential-algebraic equations (DAEs)** -- the index-reduced constrained equations of multibody mechanics -- where algebraic constraints coexist with differential states. In engineering practice they dominate wherever there is high contact/joint stiffness, thermal diffusion, chemical kinetics, or circuit-like RC behavior: settings where an explicit integrator would either crawl or blow up.
