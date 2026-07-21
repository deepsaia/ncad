The **finite element method (FEM)** is a general technique for finding approximate solutions to boundary-value problems governed by partial differential equations (PDEs). Instead of solving the PDE analytically over a continuous domain, FEM partitions the domain \(\Omega\) into a finite set of non-overlapping subdomains called *elements* (triangles, quadrilaterals, tetrahedra, hexahedra), and represents the unknown field as a piecewise combination of simple polynomial basis functions defined on those elements. This converts an infinite-dimensional problem into a finite system of algebraic equations that a computer can solve. Its power comes from geometric flexibility (arbitrary shapes and material regions) and a rigorous variational foundation that yields provable convergence and error estimates.

## Strong form to weak form

Most engineering PDEs are first written in *strong form*, requiring the solution to be smooth enough to satisfy the equation pointwise. For a scalar diffusion problem this reads

\[ -\nabla \cdot (k\,\nabla u) = f \quad \text{in } \Omega, \qquad u = \bar u \text{ on } \Gamma_D, \qquad (k\,\nabla u)\cdot \mathbf{n} = \bar q \text{ on } \Gamma_N. \]

FEM does not enforce this pointwise. Instead it multiplies the residual by an arbitrary *test* (weighting) function \(v\), integrates over the domain, and applies integration by parts (the divergence theorem). This produces the **weak form**: find \(u\) such that

\[ \int_\Omega k\,\nabla u \cdot \nabla v \, d\Omega = \int_\Omega f\,v \, d\Omega + \int_{\Gamma_N} \bar q\, v \, d\Gamma \quad \forall\, v. \]

Integration by parts lowers the differentiability required of \(u\) (one derivative instead of two) and moves the flux boundary condition into the integral naturally, which is why Neumann conditions are called *natural* and Dirichlet conditions *essential*. This weaker regularity is what allows piecewise-polynomial, only \(C^0\)-continuous approximations to be admissible.

## Shape functions and the Galerkin choice

Within each element the field is interpolated from nodal values using **shape functions** (basis functions) \(N_i\), so that \(u(\mathbf{x}) \approx \sum_i N_i(\mathbf{x})\, u_i\). The shape functions form a *partition of unity* (\(\sum_i N_i = 1\)) and satisfy the Kronecker property \(N_i(\mathbf{x}_j) = \delta_{ij}\), so the coefficients \(u_i\) are the physical values at the nodes. In the **Galerkin** method the test functions are drawn from the same space as the trial functions. Real elements are handled with an *isoparametric* mapping: the same shape functions map a reference element (in natural coordinates \(\xi,\eta,\zeta\)) to the distorted physical element, and the Jacobian of that map carries derivatives and the volume measure. Element integrals are evaluated by numerical (Gauss) quadrature at a small set of sampling points.

## Assembly and solution

Substituting the interpolation into the weak form yields, element by element, a small dense **element stiffness matrix** and load vector,

\[ K^{e}_{ij} = \int_{\Omega^e} \nabla N_i \cdot k\,\nabla N_j \, d\Omega, \qquad f^{e}_{i} = \int_{\Omega^e} f\,N_i \, d\Omega + \int_{\Gamma^e_N} \bar q\,N_i \, d\Gamma. \]

Because each global node is shared by several elements, the element contributions are **assembled** by scatter-adding them into a global system according to the element-to-node connectivity, giving the sparse linear system \(K\,\mathbf{u} = \mathbf{f}\). Essential boundary conditions are then imposed, and the system is solved by direct (sparse Cholesky/LU) or iterative (conjugate-gradient, multigrid) methods. For transient or nonlinear problems the same spatial discretization produces mass and tangent matrices that feed a time-integrator or Newton iteration. This weak-form / shape-function / assembly pipeline is identical whether the physics is structural mechanics, heat conduction, electromagnetics, or diffusion, which is why FEM is the backbone of modern computer-aided engineering.
