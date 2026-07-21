The finite element method is not the only way to discretize a PDE. Three other families dominate specific niches: the **finite difference method (FDM)**, the **finite volume method (FVM)**, and the **boundary element method (BEM)**. Each makes a different tradeoff between simplicity, conservation, and how much of the domain must be meshed, and understanding those tradeoffs is what determines which tool fits which physics.

## Finite difference method

FDM is the oldest and conceptually simplest approach: it replaces every derivative in the strong-form PDE by a difference quotient evaluated on a structured grid of points. The quotients come directly from Taylor-series expansions, which also expose the *order of accuracy*. For example, the second derivative on a uniform grid of spacing \(h\) is approximated by the central difference

\[ \left.\frac{d^2 u}{dx^2}\right|_i \approx \frac{u_{i-1} - 2u_i + u_{i+1}}{h^2} + \mathcal{O}(h^2). \]

FDM is trivial to implement and highly efficient on Cartesian or smoothly mapped structured grids, and it underpins much of classical computational physics and many high-order spectral schemes. Its weakness is geometry: representing complex, curved boundaries on a structured grid is awkward, and the basic scheme is not intrinsically conservative.

## Finite volume method

FVM discretizes the *integral* conservation form of the governing equations rather than the differential form. The domain is divided into control volumes, and the conservation law is integrated over each cell; the divergence theorem turns volume integrals of fluxes into surface integrals over cell faces:

\[ \frac{d}{dt}\int_{V} u \, dV + \oint_{\partial V} \mathbf{F}(u)\cdot \mathbf{n} \, dS = \int_{V} s \, dV. \]

Because the flux leaving one cell face is exactly the flux entering its neighbor, mass, momentum, and energy are conserved **discretely and locally**, to machine precision, regardless of mesh quality. That guaranteed conservation, together with a natural treatment of discontinuities (shocks) and arbitrary polyhedral cells, is why FVM is the dominant discretization in computational fluid dynamics and other transport problems. Its accuracy is often lower-order than a comparable FEM or spectral scheme, and achieving high order on unstructured meshes requires careful flux reconstruction.

## Boundary element method

BEM takes a fundamentally different route. For certain linear PDEs (Laplace, Helmholtz, elastostatics) with a known **fundamental solution** (Green's function) \(G\), the PDE can be recast as an integral equation posed only on the boundary \(\Gamma\), e.g.

\[ c(\mathbf{x})\,u(\mathbf{x}) + \int_{\Gamma} u\,\frac{\partial G}{\partial n}\, d\Gamma = \int_{\Gamma} G\,\frac{\partial u}{\partial n}\, d\Gamma. \]

Only the **surface** is meshed, reducing the dimensionality of the discretization by one (a 3D problem becomes a 2D surface mesh). This is a decisive advantage for exterior and infinite-domain problems such as acoustic radiation, wave scattering, potential flow, and electrostatics, where the far field is handled analytically. The cost is that the fundamental solution couples every boundary node to every other, so BEM produces **dense, non-symmetric** system matrices (mitigated by fast multipole or hierarchical-matrix acceleration), and it is largely restricted to problems where a fundamental solution exists, i.e. linear, homogeneous-region physics.
