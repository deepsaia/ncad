A single point or vector can be described in many frames, and engineering constantly needs to translate between them: a feature is authored in a local frame, a fixture defines another, an assembly imposes a third. **Change of basis** is the exact rule that re-expresses the *same* geometric quantity in a different frame, and **frame composition** is how a chain of such changes multiplies together. For orthonormal (right-handed, unit, mutually perpendicular) frames the machinery is a single rotation matrix, which is why it is both compact and numerically robust.

## The rotation matrix as a change of basis

Let frame \(B\) be a rotated copy of reference frame \(A\). Collect the three basis vectors of \(B\), written in \(A\)'s coordinates, as the columns of a matrix \({}^{A}_{B}R\). Then a point known in \(B\) is re-expressed in \(A\) by

\[ {}^{A}p = {}^{A}_{B}R\;{}^{B}p. \]

Because both frames are orthonormal, \({}^{A}_{B}R\) belongs to the **special orthogonal group** \(SO(3)\): its columns are orthonormal, so

\[ R^{\mathsf T}R = I,\qquad R^{-1}=R^{\mathsf T},\qquad \det R = +1. \]

The transpose being the inverse is the workhorse identity of the whole subject: reversing a frame change costs a transpose, not a matrix inversion, and it can never drift into a non-rotation the way a numerically inverted general matrix can. The \(\det = +1\) condition excludes reflections, preserving handedness so that a right-handed part stays right-handed.

## Composition and its non-commutativity

Frame changes chain by matrix multiplication, and the subscripts cancel like fractions:

\[ {}^{A}_{C}R = {}^{A}_{B}R\;{}^{B}_{C}R. \]

This is the backbone of a kinematic chain or an assembly tree: to place a feature defined deep in a hierarchy into world coordinates, you multiply the frame relationships from the leaf up to the root. Order matters, because \(SO(3)\) is **non-commutative**, \(R_1R_2 \ne R_2R_1\) in general, which is the algebraic reflection of the physical fact that rotating a body about \(x\) then \(y\) lands it somewhere different than \(y\) then \(x\).

## Active versus passive: one matrix, two readings

The identical matrix \(R\) supports two interpretations that must never be confused. In the **passive** (alias) reading, the point is fixed and we relabel it in a rotated frame, exactly the change of basis above. In the **active** (alibi) reading, the frame is fixed and the matrix *moves* the point to a new location, \(p' = Rp\). The two are inverses of each other for the same physical rotation angle, so a sign or transpose error here is one of the most common defects in transform code. Fixing a single convention, and stating it, is what keeps a long composition chain correct.

The practical payoff is that every frame relationship, sensor pose, datum, mounting interface, or joint, reduces to one \(SO(3)\) element, and arbitrarily long pipelines of them compose by multiplication with a transpose for every reversal. Extending each matrix with a translation column generalizes this exact structure to full rigid motions, treated separately under \(SE(3)\).
