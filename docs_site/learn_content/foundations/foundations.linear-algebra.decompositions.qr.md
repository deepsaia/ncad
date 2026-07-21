The **QR decomposition** factors a matrix \(A \in \mathbb{R}^{m\times n}\) (with \(m \ge n\)) into an orthonormal part and a triangular part,
\[
A = Q\,R, \qquad Q^{\top}Q = I, \quad R \text{ upper triangular}.
\]
The columns of \(Q\) form an orthonormal basis, and \(R\) records how the original columns of \(A\) are expressed in that basis. Because orthogonal transformations preserve the Euclidean norm, QR is the numerically preferred route for problems where conditioning matters, especially least squares.

## How it is computed

Three classical algorithms produce a QR factorization, and the choice is a stability-versus-structure trade-off. **Gram-Schmidt** orthogonalizes the columns one at a time; the *modified* variant reorders the arithmetic to resist round-off, though it is still less robust than the alternatives. **Householder reflections** apply a sequence of orthogonal transformations that zero out subdiagonal entries a whole column at a time, and this is the standard dense workhorse because the accumulated \(Q\) stays orthogonal to machine precision. **Givens rotations** zero one entry at a time, which is ideal for sparse matrices and for incrementally updating a factorization when a row or column is added, as happens in recursive estimation.

## Why it matters

The headline application is the linear least-squares problem \(\min_x \|Ax - b\|_2\). Substituting \(A = QR\) turns it into the triangular system
\[
R\,x = Q^{\top}b,
\]
solved cheaply by back-substitution. Crucially, this avoids forming the normal-equations matrix \(A^{\top}A\), whose condition number is the *square* of that of \(A\); QR keeps the conditioning of the original problem and so delivers substantially more accurate solutions for ill-conditioned fits. The orthonormal columns of \(Q\) also provide a stable basis for the column space, used whenever an orthogonal frame must be built from arbitrary spanning vectors.

Beyond fitting, QR is the core iteration of the **QR algorithm**, the standard method for computing eigenvalues of a general matrix by repeated factor-and-recombine steps that drive the matrix toward triangular form. A **rank-revealing** variant with column pivoting, \(A P = Q R\), exposes numerical rank and near-dependency among columns, which is useful for subset selection, detecting redundant constraints, and regularizing degenerate geometric fits. In short, QR is the stability-conscious counterpart to the SVD: less information, but faster to compute and sufficient for the majority of overdetermined engineering problems.
