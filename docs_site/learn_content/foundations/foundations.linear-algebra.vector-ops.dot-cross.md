The **dot product** and **cross product** are the two elementary ways to multiply vectors, and almost every geometric computation in engineering is built on one or both. They differ fundamentally in what they return: the dot product produces a scalar that measures *alignment*, while the cross product produces a vector that measures *perpendicularity and turning sense* in three dimensions.

## Dot product

For two vectors \(\mathbf{a}, \mathbf{b} \in \mathbb{R}^n\), the dot (inner, or scalar) product is
\[
\mathbf{a}\cdot\mathbf{b} = \sum_{i=1}^{n} a_i b_i = \|\mathbf{a}\|\,\|\mathbf{b}\|\cos\theta,
\]
where \(\theta\) is the angle between them. It is commutative and bilinear, and it vanishes exactly when the vectors are orthogonal. Two facts make it indispensable: the length of a vector is \(\|\mathbf{a}\| = \sqrt{\mathbf{a}\cdot\mathbf{a}}\), and the scalar projection of \(\mathbf{b}\) onto the direction \(\hat{\mathbf{a}}\) is \(\mathbf{b}\cdot\hat{\mathbf{a}}\). In practice the dot product is how software computes angles between edges, tests whether a point lies in front of or behind a plane (via the sign of \((\mathbf{p}-\mathbf{p}_0)\cdot\mathbf{n}\)), evaluates diffuse shading (\(\mathbf{n}\cdot\mathbf{l}\)), and computes mechanical work \(W = \mathbf{F}\cdot\mathbf{d}\).

## Cross product

In three dimensions the cross (vector) product returns a vector orthogonal to both operands:
\[
\mathbf{a}\times\mathbf{b} = \begin{vmatrix} \mathbf{i} & \mathbf{j} & \mathbf{k} \\ a_1 & a_2 & a_3 \\ b_1 & b_2 & b_3 \end{vmatrix}, \qquad \|\mathbf{a}\times\mathbf{b}\| = \|\mathbf{a}\|\,\|\mathbf{b}\|\sin\theta .
\]
Its magnitude equals the area of the parallelogram spanned by \(\mathbf{a}\) and \(\mathbf{b}\), and its direction follows the right-hand rule. Unlike the dot product, it is anticommutative (\(\mathbf{a}\times\mathbf{b} = -\,\mathbf{b}\times\mathbf{a}\)) and non-associative, so operand order and grouping carry meaning. It vanishes when the two vectors are parallel, which makes it a direct collinearity test.

The cross product is the standard way to build a surface normal from two tangent (or edge) vectors, to obtain a signed triangle area for orientation and winding tests, and to construct an orthonormal frame: given one axis and any second vector, \(\mathbf{a}\times\mathbf{b}\) and a further cross product yield three mutually perpendicular directions. In mechanics it expresses torque \(\boldsymbol{\tau} = \mathbf{r}\times\mathbf{F}\) and the velocity of a rotating point \(\mathbf{v} = \boldsymbol{\omega}\times\mathbf{r}\). Note that the cross product is special to three dimensions (with a seven-dimensional curiosity); the general, dimension-independent replacement is the exterior/wedge product, whose antisymmetry the cross product inherits.

<svg viewBox="0 0 240 120" width="240" height="120" stroke="currentColor" fill="none" stroke-width="1.5">
  <line x1="20" y1="100" x2="140" y2="100"/>
  <line x1="20" y1="100" x2="70" y2="30"/>
  <line x1="140" y1="100" x2="70" y2="30" stroke-dasharray="4 3"/>
  <text x="90" y="116" font-size="11" stroke="none" fill="currentColor">a</text>
  <text x="36" y="62" font-size="11" stroke="none" fill="currentColor">b</text>
  <text x="70" y="78" font-size="10" stroke="none" fill="currentColor">area = |a x b|</text>
</svg>
