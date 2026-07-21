**Eigendecomposition** answers the question: along which directions does a linear operator act purely as a scaling? A nonzero vector \(\mathbf{v}\) is an *eigenvector* of a square matrix \(A\) with *eigenvalue* \(\lambda\) when
\[
A\,\mathbf{v} = \lambda\,\mathbf{v}.
\]
When \(A\) has a full set of independent eigenvectors it is diagonalizable, \(A = V\Lambda V^{-1}\), where the columns of \(V\) are the eigenvectors and \(\Lambda\) is the diagonal matrix of eigenvalues. This separates the operator into a change of basis, a scaling along each eigen-direction, and a change back, which is why the eigenbasis is the natural coordinate system for understanding what a transformation does.

## Symmetric matrices and the spectral theorem

Most eigenproblems in engineering involve **symmetric** matrices, and there the structure is especially clean. The spectral theorem guarantees that a real symmetric matrix has real eigenvalues and a full set of mutually orthogonal eigenvectors, so it factors as
\[
A = Q\,\Lambda\,Q^{\top}, \qquad Q^{\top}Q = I.
\]
The eigenvectors are the *principal directions* and the eigenvalues are the *principal values*. This is exactly the mathematics behind principal moments of inertia (eigenvalues of the inertia tensor), principal stresses and strains (eigenvalues of the stress or strain tensor), and principal curvatures of a surface (eigenvalues of the shape operator). In each case the eigendecomposition rotates into the frame where the tensor is diagonal and the off-diagonal coupling disappears.

## Computation and vibration analysis

Although eigenvalues are defined by the characteristic polynomial \(\det(A - \lambda I) = 0\), that route is numerically useless beyond tiny matrices; practical solvers use the QR algorithm for dense problems and Lanczos or Arnoldi iterations for large sparse ones, often seeking only a few extreme eigenpairs. A central engineering use is **modal analysis**, which solves the generalized eigenproblem
\[
K\,\boldsymbol{\phi} = \omega^{2}\,M\,\boldsymbol{\phi},
\]
where \(K\) is stiffness and \(M\) is mass; the eigenvalues give natural frequencies \(\omega\) and the eigenvectors give mode shapes. The same spectral idea drives buckling analysis, stability of dynamical systems (eigenvalues of the Jacobian), and principal component analysis (eigenvectors of a covariance matrix).

It is worth contrasting eigendecomposition with the SVD. Eigendecomposition applies only to square matrices and may involve complex values or fail to diagonalize (defective matrices); the SVD applies to any matrix and always exists with real, non-negative singular values. For a symmetric positive semi-definite matrix the two coincide, with eigenvalues equal to singular values. Choosing eigendecomposition signals that the *invariant directions and their scalings* are the object of interest, as opposed to the input-output geometry the SVD describes.
