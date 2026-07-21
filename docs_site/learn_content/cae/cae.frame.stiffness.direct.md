The **direct stiffness method** (DSM) is the matrix formulation of structural analysis that underlies essentially every truss and frame solver in use today. It treats a structure as an assembly of discrete members joined at nodes, relates the displacements of those nodes to the forces applied to them through a **stiffness matrix**, and reduces the analysis to the solution of one linear system. Its power is bookkeeping: element behavior is written once in a member-local frame, transformed into a common global frame, and then simply *added* into the right locations of a global matrix according to which degrees of freedom each member connects.

## The core relationship

For the whole structure, the method enforces

\[ \mathbf{K}\,\mathbf{u} = \mathbf{f}, \]

where \( \mathbf{u} \) collects the nodal displacements and rotations (degrees of freedom, DOF), \( \mathbf{f} \) collects the nodal forces and moments, and \( \mathbf{K} \) is the assembled global stiffness matrix. At the element level, the stiffness matrix is derived from the beam theory in use. The simplest case, an axial bar of stiffness \(EA/L\) with one DOF per node, gives

\[ \mathbf{k}_\ell = \frac{EA}{L}\begin{bmatrix} 1 & -1 \\ -1 & 1 \end{bmatrix}. \]

A general three-dimensional frame member has six DOF per node (three translations, three rotations), producing a \(12 \times 12\) local matrix that superposes axial (\(EA/L\)), torsional (\(GJ/L\)), and bending terms (\(EI/L\) groups) in the two principal planes.

## Transformation and assembly

Because each member is oriented arbitrarily in space, its local matrix must be rotated into the global coordinate frame before the contributions from different members can be combined. With an orthogonal transformation matrix \( \mathbf{T} \) built from the member's direction cosines,

\[ \mathbf{k}_g = \mathbf{T}^{\mathsf T}\,\mathbf{k}_\ell\,\mathbf{T}. \]

Assembly then scatters each \( \mathbf{k}_g \) into the global matrix by adding its entries to the rows and columns of the DOF it touches; shared nodes accumulate contributions from every member framing into them, which is exactly how compatibility (shared displacements) and equilibrium (summed forces) are enforced. The resulting \( \mathbf{K} \) is symmetric, sparse, and, before boundary conditions are applied, **singular**, because the unrestrained structure still possesses rigid-body modes.

## Boundary conditions and solution

Supports are imposed by partitioning the DOF into free (\(f\)) and restrained/supported (\(s\)) sets:

\[ \begin{bmatrix} \mathbf{K}_{ff} & \mathbf{K}_{fs} \\ \mathbf{K}_{sf} & \mathbf{K}_{ss} \end{bmatrix} \begin{bmatrix} \mathbf{u}_f \\ \mathbf{u}_s \end{bmatrix} = \begin{bmatrix} \mathbf{f}_f \\ \mathbf{r}_s \end{bmatrix}. \]

With prescribed support displacements \( \mathbf{u}_s \) (often zero) known, the free displacements follow from the reduced system \( \mathbf{K}_{ff}\,\mathbf{u}_f = \mathbf{f}_f - \mathbf{K}_{fs}\,\mathbf{u}_s \). Restraining enough DOF to remove all rigid-body modes makes \( \mathbf{K}_{ff} \) positive definite, so a Cholesky or sparse LU factorization solves it robustly. Loads that act along a member (distributed pressure, self-weight, thermal strain) are first converted to statically equivalent **fixed-end forces** applied at the nodes, so that all loading enters through the nodal vector \( \mathbf{f} \).

The method's significance is historical as well as practical: the systematic element-by-element assembly of a global stiffness matrix, published for aircraft structures in the mid-1950s, is the direct ancestor of the finite element method. Its determinism, sparsity, and clean separation between element formulation and global bookkeeping are why it remains the backbone of frame, truss, and general structural solvers.
