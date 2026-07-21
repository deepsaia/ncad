The equations of motion of a multibody system are ordinary differential equations (ODEs), or more generally differential-algebraic equations (DAEs) when joints impose constraints. In descriptor form they read

\[ M(q)\,\ddot q = f(q,\dot q, t) - G(q)^{\mathsf T}\lambda, \qquad g(q) = 0, \]

where \(M\) is the mass matrix, \(f\) collects applied and gyroscopic forces, \(g\) are the position constraints and \(G=\partial g/\partial q\) their Jacobian, with Lagrange multipliers \(\lambda\) enforcing them. A time integrator advances the state \(y=(q,\dot q)\) from \(t_n\) to \(t_{n+1}=t_n+h\). The single most consequential choice about that integrator is whether it is *explicit* or *implicit*.

## The distinction

An **explicit** method computes the new state purely from quantities already known at the current step. The archetype is forward (explicit) Euler,

\[ y_{n+1} = y_n + h\, F(t_n, y_n), \]

where \(F\) is the right-hand side of \(\dot y = F(t,y)\). Each step is a direct evaluation, so it is cheap and trivial to code; explicit Runge-Kutta families (RK4, Dormand-Prince) simply take several such evaluations per step. An **implicit** method instead defines the new state through an equation in which the unknown appears on both sides. Backward (implicit) Euler is

\[ y_{n+1} = y_n + h\, F(t_{n+1}, y_{n+1}). \]

Because \(F\) is generally nonlinear in \(y_{n+1}\), each step requires solving a nonlinear algebraic system, typically by Newton iteration, which in turn needs the Jacobian \(\partial F/\partial y\) and a linear solve per iteration. An implicit step therefore costs far more per step than an explicit one.

## Why implicit methods earn their cost: stability

The payoff is numerical stability. Applying a one-step method to the scalar test equation \(\dot y = \mu y\) (where \(\mu\) stands in for an eigenvalue of the Jacobian) yields \(y_{n+1} = R(h\mu)\,y_n\), and the method is stable only where the *amplification factor* satisfies \(|R(h\mu)|\le 1\). For forward Euler \(R(z)=1+z\), whose stability region is the disk \(|1+z|\le 1\): a small bounded set that forces the step \(h\) to shrink as the fastest \(|\mu|\) grows, *regardless of accuracy needs*. For backward Euler \(R(z)=1/(1-z)\), which is bounded by 1 for the entire left half-plane \(\Re(z)\le 0\). A method whose stability region contains the whole left half-plane is called **A-stable**; such methods place no stability-driven ceiling on \(h\) for decaying modes.

<svg viewBox="0 0 360 150" width="360" height="150" stroke="currentColor" fill="none" stroke-width="1.2">
  <line x1="20" y1="75" x2="170" y2="75"/><line x1="70" y1="20" x2="70" y2="130"/>
  <circle cx="45" cy="75" r="25"/>
  <text x="30" y="145" font-size="10" stroke="none" fill="currentColor">explicit Euler region</text>
  <line x1="200" y1="75" x2="350" y2="75"/><line x1="290" y1="20" x2="290" y2="130"/>
  <rect x="200" y="25" width="90" height="100"/>
  <text x="210" y="145" font-size="10" stroke="none" fill="currentColor">A-stable (whole left half-plane)</text>
</svg>

## Where the choice matters

The rule of thumb follows directly. If the dynamics are *non-stiff*, meaning the timescales you must resolve for accuracy are comparable to the fastest ones present, an explicit method wins: many cheap steps beat few expensive ones. This covers most free-flight rigid-body motion, orbital mechanics, and gentle articulated linkages. If the system is *stiff*, meaning it contains fast modes (stiff springs, bushings, penalty contact, tightly regularized joints) that decay far faster than the motion of interest, an explicit method is throttled by stability to steps far smaller than accuracy would require, and an implicit A-stable or L-stable method (backward Euler, the BDF family, implicit Runge-Kutta, or in structural dynamics the Newmark/HHT-\(\alpha\) schemes) is dramatically more efficient despite its per-step expense. Many production solvers hedge with *semi-implicit* or *IMEX* schemes that treat only the stiff terms implicitly, and with adaptive step-size control that grows \(h\) when the local error estimate permits.
