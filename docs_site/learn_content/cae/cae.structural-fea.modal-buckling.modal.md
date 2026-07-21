Modal analysis computes the natural frequencies at which an unforced structure prefers to vibrate and the mode shapes it takes while doing so. These are intrinsic properties of the structure, independent of any particular load, and they are the foundation of nearly all structural dynamics: resonance avoidance, noise and vibration engineering, and the reduced bases used for transient and frequency-response solutions all start here.

## The generalized eigenproblem

Starting from the undamped free-vibration equation \(\mathbf{M}\ddot{\mathbf{u}}+\mathbf{K}\mathbf{u}=\mathbf{0}\) and assuming a synchronous harmonic motion \(\mathbf{u}(t)=\boldsymbol{\phi}\,e^{i\omega t}\), the time dependence cancels and the problem becomes the generalized symmetric eigenproblem

\[ \mathbf{K}\,\boldsymbol{\phi}_i = \omega_i^{2}\,\mathbf{M}\,\boldsymbol{\phi}_i . \]

Each eigenvalue \(\omega_i^2\) gives a natural angular frequency \(\omega_i\) (and cyclic frequency \(f_i=\omega_i/2\pi\)); the eigenvector \(\boldsymbol{\phi}_i\) is the corresponding mode shape, a relative deflection pattern with no absolute amplitude. Because \(\mathbf{K}\) and \(\mathbf{M}\) are symmetric, the frequencies are real and the modes are orthogonal with respect to both matrices, \(\boldsymbol{\phi}_i^{\mathsf T}\mathbf{M}\boldsymbol{\phi}_j=0\) and \(\boldsymbol{\phi}_i^{\mathsf T}\mathbf{K}\boldsymbol{\phi}_j=0\) for \(i\neq j\). That orthogonality is what lets modal superposition diagonalize the equations of motion into a set of independent single-degree-of-freedom oscillators.

## Mass matrices and rigid-body modes

The mass matrix can be **consistent** (formed with the same shape functions as the stiffness, \(\mathbf{M}^e=\int \rho\,\mathbf{N}^{\mathsf T}\mathbf{N}\,d\Omega\)) or **lumped** (mass concentrated at nodes, giving a diagonal matrix that is cheaper and essential for explicit dynamics). A structure that is free or partly unconstrained possesses rigid-body modes with \(\omega=0\); their presence is expected for free-free models and is a red flag for a model that was meant to be grounded.

## Solvers, participation, and use

Only the lowest handful of modes usually matter, so full eigen-decomposition is avoided in favor of partial extraction: Lanczos iteration and subspace iteration, often with a spectral shift to target a frequency band, return the requested modes efficiently for large sparse systems. To judge how many modes are enough, analysts inspect modal participation factors and effective modal mass, which quantify how strongly each mode couples to a given excitation direction; a common target is that the retained modes capture the large majority of the total mass. In application, modal results tell a designer whether operating frequencies (rotating machinery, road input, acoustic excitation) sit dangerously close to a natural frequency, and they supply the compact modal basis on which efficient transient and harmonic analyses are built.
