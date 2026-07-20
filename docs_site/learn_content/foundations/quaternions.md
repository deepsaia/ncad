A **unit quaternion** encodes a 3D rotation as four numbers, $q = w + x\,i + y\,j + z\,k$ with
$\lVert q \rVert = 1$, where $i, j, k$ are the imaginary units satisfying $i^2 = j^2 = k^2 = ijk =
-1$. A rotation by angle $\theta$ about a unit axis $\hat{n} = (n_x, n_y, n_z)$ is

\[
q = \cos\tfrac{\theta}{2} + \sin\tfrac{\theta}{2}\,(n_x i + n_y j + n_z k).
\]

A vector is rotated by the sandwich product $v' = q\,v\,q^{-1}$ (treating $v$ as a pure
quaternion), and rotations compose by quaternion multiplication, in the same order as the
equivalent matrix product.

## Why quaternions are preferred for orientation

Unit quaternions are the standard internal representation for orientation in kinematics and
graphics for three reasons:

- **No gimbal lock.** Unlike Euler angles, quaternions have no orientation at which a degree of
  freedom collapses.
- **Cheap, stable composition.** Multiplying two quaternions is fewer operations than multiplying
  two matrices, and renormalizing a drifted quaternion is a single division by its norm, far
  cheaper than re-orthonormalizing a matrix.
- **Smooth interpolation.** Spherical linear interpolation (**slerp**) between two orientations
  follows the shortest great-circle arc on the unit sphere $S^3$, giving constant-rate,
  singularity-free blends, the basis of orientation keyframing.

## The double cover

The map from unit quaternions to rotations is two-to-one: $q$ and $-q$ represent the *same*
rotation ($S^3$ double-covers $SO(3)$). Code that compares or interpolates orientations must handle
this sign ambiguity, for slerp, negate one quaternion when their dot product is negative so the
interpolation takes the short way around.
