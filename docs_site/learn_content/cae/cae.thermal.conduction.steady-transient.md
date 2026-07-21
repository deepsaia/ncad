Heat conduction analysis predicts how thermal energy diffuses through a solid body and how its temperature field evolves. It rests on **Fourier's law**, which states that the local heat flux vector is proportional to the negative temperature gradient,

\[ \mathbf{q} = -k\,\nabla T, \]

where \(k\) is the thermal conductivity (a scalar for isotropic materials, a tensor for anisotropic ones). Combining Fourier's law with conservation of energy over a control volume yields the governing **heat diffusion equation**,

\[ \rho\,c_p\,\frac{\partial T}{\partial t} = \nabla \cdot (k\,\nabla T) + \dot{Q}, \]

where \(\rho\) is density, \(c_p\) is specific heat, and \(\dot{Q}\) is a volumetric heat-generation rate (Joule heating, chemical reaction, nuclear decay). This single parabolic partial differential equation, together with its boundary and initial conditions, defines the entire class of conduction problems.

## Steady state versus transient

A **steady-state** analysis drops the time-derivative term: the temperature field no longer changes, so \(\nabla \cdot (k\nabla T) + \dot{Q} = 0\). With constant conductivity and no source this reduces to Laplace's equation \(\nabla^2 T = 0\); with a source it becomes Poisson's equation. Steady state answers "where does the heat finally settle?" and is the natural model for a component running at a fixed operating point. A **transient** analysis retains \(\rho c_p\,\partial T/\partial t\) and answers "how fast does it get there, and what peaks occur on the way?" The controlling material property is the **thermal diffusivity** \(\alpha = k/(\rho c_p)\); the dimensionless **Fourier number** \(\mathrm{Fo} = \alpha t / L^2\) measures how far a thermal front has penetrated a length scale \(L\) in time \(t\), so \(\mathrm{Fo}\approx 1\) marks the transition toward the steady solution.

## Finite-element discretization

Applying a Galerkin weighted-residual (or equivalent variational) statement to the heat equation and interpolating temperature with element shape functions \(T \approx \mathbf{N}\,\mathbf{T}_e\) produces the semi-discrete system

\[ \mathbf{C}\,\dot{\mathbf{T}} + \mathbf{K}\,\mathbf{T} = \mathbf{F}, \]

where \(\mathbf{K}\) is the **conductivity (stiffness) matrix**, \(\mathbf{C}\) is the **heat-capacity (mass) matrix** carrying the \(\rho c_p\) storage term, and \(\mathbf{F}\) assembles internal generation and boundary fluxes. A steady analysis solves the linear (or, for temperature-dependent \(k\), nonlinear) system \(\mathbf{K}\,\mathbf{T} = \mathbf{F}\) directly. The same \(\mathbf{K}\), \(\mathbf{C}\), and \(\mathbf{F}\) serve both regimes, which is why one mesh and one material model feed either study.

## Time integration and stability

Transient conduction is marched forward with a one-step **generalized-trapezoidal (\(\theta\)-method)** scheme,

\[ \mathbf{C}\,\frac{\mathbf{T}_{n+1}-\mathbf{T}_n}{\Delta t} + \mathbf{K}\big[(1-\theta)\mathbf{T}_n + \theta\,\mathbf{T}_{n+1}\big] = \mathbf{F}_{n+\theta}. \]

Setting \(\theta = 0\) gives explicit forward Euler (cheap per step but only conditionally stable, requiring \(\Delta t\) below a critical value tied to the smallest element and \(\alpha\)); \(\theta = 1\) gives backward Euler, unconditionally stable and strongly damping; \(\theta = \tfrac{1}{2}\) gives Crank-Nicolson, second-order accurate but prone to oscillation on coarse time steps. Practical solvers favor backward Euler for robustness on stiff, sharply loaded problems and often use automatic time-step control driven by the local rate of temperature change. Because the underlying operator is diffusive, refining both mesh and time step converges monotonically toward the exact field, and this convergence, together with energy-balance checks (heat in minus heat out equals stored energy), is the standard way to trust a conduction result.
