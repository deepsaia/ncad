The **scalar triple product** and **vector triple product** combine three vectors and answer two questions that come up constantly in geometry: *how much volume do three directions enclose*, and *how do nested rotations and projections collapse*. Both reduce to dot and cross products, but recognizing them as named identities avoids redundant computation and clarifies intent.

## Scalar triple product

The scalar triple product is
\[
[\mathbf{a},\mathbf{b},\mathbf{c}] = \mathbf{a}\cdot(\mathbf{b}\times\mathbf{c}) = \det\!\begin{bmatrix} a_1 & a_2 & a_3 \\ b_1 & b_2 & b_3 \\ c_1 & c_2 & c_3 \end{bmatrix}.
\]
Its absolute value is the volume of the parallelepiped spanned by the three vectors, and its **sign** encodes handedness (positive for a right-handed triple, negative for left-handed). Because it equals a determinant, it is invariant under cyclic permutation, \(\mathbf{a}\cdot(\mathbf{b}\times\mathbf{c}) = \mathbf{b}\cdot(\mathbf{c}\times\mathbf{a}) = \mathbf{c}\cdot(\mathbf{a}\times\mathbf{b})\), and it changes sign under a swap of any two vectors. It is zero exactly when the three vectors are linearly dependent (coplanar), which makes it the cleanest coplanarity and orientation test available.

In engineering software this identity drives signed tetrahedron volume \(V = \tfrac{1}{6}\,[\mathbf{b}-\mathbf{a},\,\mathbf{c}-\mathbf{a},\,\mathbf{d}-\mathbf{a}]\), which in turn feeds closed-mesh volume and centroid computation (summing signed tetrahedra from a reference point), robust in/out orientation of solids, and barycentric coordinate evaluation. Numerically it is worth noting that this determinant can lose precision when the three vectors are nearly coplanar, so a small nonzero result should be interpreted through a tolerance rather than as strict non-degeneracy.

## Vector triple product

The vector triple product satisfies the expansion known as the BAC-CAB rule:
\[
\mathbf{a}\times(\mathbf{b}\times\mathbf{c}) = \mathbf{b}\,(\mathbf{a}\cdot\mathbf{c}) - \mathbf{c}\,(\mathbf{a}\cdot\mathbf{b}).
\]
The result lies in the plane spanned by \(\mathbf{b}\) and \(\mathbf{c}\), which is geometrically intuitive since \(\mathbf{b}\times\mathbf{c}\) is normal to that plane and crossing again brings the result back into it. The identity is the workhorse for simplifying expressions in rigid-body dynamics (for example the centripetal term \(\boldsymbol{\omega}\times(\boldsymbol{\omega}\times\mathbf{r})\)), for decomposing a vector into components parallel and perpendicular to an axis, and for reflecting or projecting directions without forming an explicit matrix. It also underlies the Jacobi identity, \(\mathbf{a}\times(\mathbf{b}\times\mathbf{c}) + \mathbf{b}\times(\mathbf{c}\times\mathbf{a}) + \mathbf{c}\times(\mathbf{a}\times\mathbf{b}) = \mathbf{0}\), the structural relation that makes \(\mathbb{R}^3\) under the cross product a Lie algebra.
