**Euler's rotation theorem** states that any orientation of a rigid body about a fixed point is achievable by a *single* rotation through some angle \(\theta\) about some fixed axis \(\hat{\omega}\). The **axis-angle** representation takes this literally: an orientation is a unit axis plus a scalar angle, often packed into a single **rotation vector** \(\hat{\omega}\theta\in\mathbb{R}^3\) whose direction is the axis and whose magnitude is the angle. This is the minimal, most geometrically direct account of a rotation, and it is the bridge between rotations and the exponential map on the Lie group \(SO(3)\).

## Rodrigues' rotation formula

To turn an axis and angle into a matrix, encode the axis as the **skew-symmetric** matrix

\[ [\hat{\omega}] = \begin{bmatrix} 0 & -\hat{\omega}_3 & \hat{\omega}_2 \\ \hat{\omega}_3 & 0 & -\hat{\omega}_1 \\ -\hat{\omega}_2 & \hat{\omega}_1 & 0 \end{bmatrix},\qquad [\hat{\omega}]v = \hat{\omega}\times v. \]

Rodrigues' formula then builds the rotation matrix in closed form:

\[ R = I + \sin\theta\,[\hat{\omega}] + (1-\cos\theta)\,[\hat{\omega}]^2. \]

Applied to a vector this is the same as decomposing \(v\) into parts along and across the axis and turning only the perpendicular part:

\[ v_{\text{rot}} = v\cos\theta + (\hat{\omega}\times v)\sin\theta + \hat{\omega}(\hat{\omega}\cdot v)(1-\cos\theta). \]

## The exponential and logarithm maps

Rodrigues' formula is precisely the closed-form matrix exponential of the skew matrix, which is why axis-angle is the natural coordinate on \(SO(3)\):

\[ R = \exp\!\big(\theta[\hat{\omega}]\big),\qquad \theta[\hat{\omega}]\in\mathfrak{so}(3). \]

The skew-symmetric matrices form the Lie algebra \(\mathfrak{so}(3)\), the tangent space at the identity, and they are exactly the infinitesimal generators of rotation, i.e. angular velocity. The inverse (logarithm) recovers the axis and angle from a matrix:

\[ \theta = \arccos\!\left(\frac{\operatorname{tr}(R)-1}{2}\right),\qquad [\hat{\omega}] = \frac{1}{2\sin\theta}\,(R-R^{\mathsf T}). \]

## Strengths, singularities, and use

The representation carries no handedness ambiguity and its three numbers have a clean physical meaning, which makes it the standard for *composing small increments*, integrating angular velocity, and interpolating orientation. It is not free of singularities: the axis is undefined at \(\theta=0\) (any axis works), and the log map is delicate near \(\theta=\pi\) where \(\sin\theta\to 0\), so robust implementations special-case those two angles. In practice axis-angle underpins angular-velocity integration, spring-like orientation errors in control, and it converts cheaply to and from unit quaternions (\(q=(\cos\tfrac{\theta}{2},\,\hat{\omega}\sin\tfrac{\theta}{2})\)), which is why the two are usually used together: axis-angle for the geometry and the increment, quaternions for numerically stable storage.
