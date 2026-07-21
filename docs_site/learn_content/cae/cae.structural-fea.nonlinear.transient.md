Transient (time-history) dynamic analysis computes how a structure moves and stresses evolve as functions of time when inertia and, usually, damping cannot be neglected. It is the tool for impacts, blasts, drop tests, shock, seismic input, and any loading whose time scale is comparable to the structure's own vibration periods. Where linear static analysis drops the time derivatives, transient analysis keeps them.

## The semi-discrete equation of motion

Spatial finite-element discretization of a dynamic problem yields a system of coupled second-order ordinary differential equations in time,

\[ \mathbf{M}\,\ddot{\mathbf{u}}(t) + \mathbf{C}\,\dot{\mathbf{u}}(t) + \mathbf{K}\,\mathbf{u}(t) = \mathbf{f}(t), \]

with \(\mathbf{M}\) the mass matrix, \(\mathbf{C}\) the damping matrix, \(\mathbf{K}\) the stiffness, and \(\mathbf{f}(t)\) the time-varying load. Damping is often idealized as Rayleigh (proportional) damping, \(\mathbf{C}=\alpha\mathbf{M}+\beta\mathbf{K}\), because that form is diagonalized by the same modes as the undamped system. The equation is integrated forward in time either directly or after projection onto a modal basis (modal transient analysis), the latter being efficient for lightly damped linear structures dominated by a few modes.

## Implicit versus explicit time integration

Direct integration marches the solution in steps of size \(\Delta t\), and the choice of scheme is fundamental. **Implicit** methods, such as the Newmark-beta family and the HHT-alpha method, evaluate equilibrium at the end of the step and therefore require solving a system of equations (a factorization) every step; with suitable parameters they are unconditionally stable, so \(\Delta t\) is limited by accuracy rather than stability. They suit structural dynamics and slower transients where relatively large steps are acceptable. **Explicit** methods, principally central difference, evaluate equilibrium at the known state and, with a lumped (diagonal) mass matrix, need no factorization at all, making each step very cheap. The price is conditional stability: the step must satisfy a Courant-type limit tied to the highest frequency, roughly \(\Delta t \le \Delta t_{\text{cr}} \approx L_{\min}/c\), the time a dilatational wave of speed \(c=\sqrt{E/\rho}\) takes to cross the smallest element. Explicit integration is the standard for very fast, highly nonlinear events (impact, crash, penetration) where tiny steps are unavoidable anyway.

## Practical considerations

The governing trade-off is cost per step against number of steps and stability. Implicit schemes take few expensive steps; explicit schemes take many cheap ones, and their stability limit means a single over-refined element can throttle the entire run. Analysts must also introduce a physically defensible amount of damping and, for wave and shock problems, ensure the mesh resolves the wavelengths of interest (typically several elements per wavelength) so the discretization does not artificially disperse or filter the signal. Verification leans on energy balance over the history and on comparison of extracted response spectra or peak responses against refined runs.
