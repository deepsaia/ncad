**Plücker coordinates** are the standard way to describe a *line* in three-dimensional space using six numbers, and they are the geometric foundation on which screws, twists, and wrenches are built. A line has four degrees of freedom, yet representing it by a point and a direction is awkward because the choice of point is arbitrary. Plücker coordinates resolve this by pairing the line's direction with its moment about the origin.

## Coordinates of a line

Given any point \(r\) on the line and a direction \(d\), the Plücker coordinates are the two 3-vectors

\[
(\,d\ ;\ m\,), \qquad m = r \times d,
\]

where \(m\), the *moment vector*, is independent of which point \(r\) on the line is chosen (adding a multiple of \(d\) to \(r\) leaves \(r\times d\) unchanged). The six numbers are homogeneous (scaling both parts describes the same line) and they satisfy the single quadratic **Plücker constraint**

\[
d^\top m = 0,
\]

which expresses that a genuine line's direction and moment are perpendicular. The set of all lines therefore forms a 4-dimensional quadric (the Klein quadric) inside 5-dimensional projective space, and incidence, distance, and intersection tests reduce to simple bilinear expressions in these coordinates.

## From lines to screws

A **screw** generalizes a line by attaching a scalar **pitch** \(h\). Where a line's two 3-vectors are orthogonal, a screw relaxes that: taking a unit direction \(s\) through a point \(s_0\) with pitch \(h\), the screw coordinates are

\[
\$ = \begin{bmatrix} s \\ s_0 \times s + h\,s \end{bmatrix}.
\]

The extra term \(h\,s\) breaks the Plücker orthogonality by exactly the amount that encodes the pitch, so a screw is a line with a superimposed translation-per-rotation. When \(h=0\) the screw is a pure line; when \(h\to\infty\) it degenerates to a free direction. Every twist and every wrench is a *screw with magnitude*: a twist is a screw times an angular rate, a wrench is a screw times a force magnitude. This is why the same six-number machinery serves both velocity and force.

Historically this framework is due to Ball's treatise on the theory of screws, which unified the kinematics of Chasles and the statics of Poinsot into one algebra of six-vectors. Its practical payoff is that lines, axes, and loads become first-class algebraic objects: joint axes are Plücker lines, the reciprocity of screws (the vanishing of the *reciprocal product* \(s_1^\top m_2 + s_2^\top m_1\)) tells you when a motion transmits no power against a constraint, and line geometry underlies robust tests for parallelism, intersection, and common normals in mechanism design, computational geometry, and multibody constraint modeling.
