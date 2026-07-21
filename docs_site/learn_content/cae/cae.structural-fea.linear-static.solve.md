Linear static analysis computes the deformed configuration of a structure held in static equilibrium under time-invariant loads, under the assumption that response is linear. After discretizing the domain into finite elements, the continuous equilibrium problem collapses to a single system of algebraic equations,

\[ \mathbf{K}\,\mathbf{u} = \mathbf{f}, \]

where \(\mathbf{K}\) is the global stiffness matrix, \(\mathbf{u}\) the vector of unknown nodal displacements (and rotations, for structural elements), and \(\mathbf{f}\) the vector of equivalent nodal loads. It is the workhorse of structural simulation: fast, robust, and the correct model whenever loads are quasi-static and the structure stays firmly in its linear regime.

## From the continuum to Ku = f

The equation is the discrete form of the principle of virtual work (equivalently, stationarity of the total potential energy). Within each element the displacement field is interpolated from nodal values through shape functions \(\mathbf{N}\), so strains follow from the strain-displacement operator \(\mathbf{B}\) as \(\boldsymbol{\varepsilon}=\mathbf{B}\mathbf{u}^e\). Substituting the linear-elastic constitutive law \(\boldsymbol{\sigma}=\mathbf{D}\boldsymbol{\varepsilon}\) yields the element stiffness

\[ \mathbf{K}^e = \int_{\Omega^e} \mathbf{B}^{\mathsf T}\,\mathbf{D}\,\mathbf{B}\; d\Omega, \]

usually evaluated by Gauss quadrature. Element matrices are then scattered into their global degrees of freedom (assembly), and body forces, surface tractions, and point loads are lumped into \(\mathbf{f}\) by the same interpolation, guaranteeing that the discrete loads are work-equivalent to the physical ones.

## The three assumptions of linearity

Validity rests on three independent linearity assumptions. Geometric linearity: displacements and strains are small enough that \(\mathbf{B}\) and the reference geometry are treated as fixed (no stress stiffening, no large rotation). Material linearity: the constitutive matrix \(\mathbf{D}\) is constant, i.e. Hooke's law with no yielding. Boundary linearity: constraints and load directions do not change with deformation (no evolving contact, no follower forces). When all three hold, superposition applies and the solution is unique. Violating any one of them is precisely what defines a nonlinear problem.

## Solving and post-processing

After essential (displacement) boundary conditions remove the rigid-body modes, \(\mathbf{K}\) is symmetric and positive definite; an unconstrained or under-constrained model leaves \(\mathbf{K}\) singular, which surfaces as zero-energy (rigid-body) modes and a failed factorization. Direct solvers exploit sparsity and symmetry (Cholesky or \(\mathbf{LDL}^{\mathsf T}\) factorization) and are the default for small-to-medium models; iterative solvers (preconditioned conjugate gradient, algebraic multigrid) scale better to very large models. Once \(\mathbf{u}\) is known, element strains \(\boldsymbol{\varepsilon}=\mathbf{B}\mathbf{u}\), stresses \(\boldsymbol{\sigma}=\mathbf{D}\boldsymbol{\varepsilon}\), reaction forces, and derived scalars such as the von Mises stress follow directly.

Sound practice treats the number as provisional until it is verified: check that reactions balance the applied load, perform mesh refinement to confirm convergence of the quantity of interest, and treat stresses at reentrant corners or point loads with suspicion, since the exact elastic solution is singular there and the mesh only reports an artifact that grows without bound as elements shrink.
