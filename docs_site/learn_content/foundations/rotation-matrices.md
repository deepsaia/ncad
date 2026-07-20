A **rotation matrix** is an orthonormal $3\times3$ matrix that reorients vectors of 3D space
about the origin while preserving lengths and angles. The set of all such matrices forms the
**special orthogonal group** $SO(3)$: matrices $R$ satisfying

\[
R^\top R = I, \qquad \det R = +1 .
\]

The first condition (orthonormality) makes the columns a right-handed orthonormal basis, the
axes of the rotated frame expressed in the original frame. The determinant condition $+1$ excludes
reflections (which have $\det = -1$), so a rotation never turns a right-handed part into its mirror
image. A vector $v$ is rotated by matrix multiplication, $v' = R v$, and rotations compose by
matrix product: applying $R_1$ then $R_2$ is the single rotation $R_2 R_1$. Because matrix
multiplication does not commute, **rotation order matters**, $R_2 R_1 \neq R_1 R_2$ in general.

## Why it is the workhorse representation

Rotation matrices are the representation every other rotation form lowers to. Euler angles,
axis-angle, and unit quaternions all convert to a matrix to actually transform geometry, because
the matrix acts directly and unambiguously on coordinates. A matrix carries no singularities
(unlike Euler angles) and no sign ambiguity (unlike quaternions, where $q$ and $-q$ denote the same
rotation), at the cost of nine numbers constrained by six equations, so it is redundant to store
but trivial to apply.

## Orthonormalization drift

Repeatedly multiplying rotation matrices in floating point slowly erodes orthonormality: the
product drifts off $SO(3)$. Long chains re-project back onto the group (for example via the polar
decomposition or Gram-Schmidt) to keep $R^\top R = I$ to tolerance. This is the rotational analogue
of the geometric-robustness concern that runs through all of CAD.
