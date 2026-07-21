**Euler angles** parameterize an orientation as a sequence of three elementary rotations about coordinate axes. Their appeal is human: three named angles such as roll, pitch, and yaw map directly onto how people describe how a body is turned. This intuitiveness is also their weakness, because the three-parameter description of a fundamentally three-dimensional but curved rotation space cannot be globally smooth, and the defect surfaces as **gimbal lock**.

## Sequences and conventions

A rotation is built by composing three axis rotations, for example the aerospace \(z\!-\!y\!-\!x\) (yaw α, pitch β, roll γ) sequence:

\[ R = R_z(\alpha)\,R_y(\beta)\,R_x(\gamma). \]

There are **twelve** valid three-axis conventions, split into *proper Euler angles* that repeat an axis (z-x-z, z-y-z, ...) and *Tait–Bryan angles* that use all three (z-y-x, x-y-z, ...). Two further choices double the ambiguity: **intrinsic** rotations act about the body's own moving axes, while **extrinsic** rotations act about the fixed world axes, and an intrinsic sequence equals the reverse-order extrinsic sequence. Because six choices multiply out to many distinct interpretations of the same three numbers, an angle triple is meaningless without its stated convention, and mismatched conventions are a classic source of silent orientation errors in data exchange.

## Gimbal lock

Euler angles are a *chart* on the rotation manifold, and every three-angle chart has singular configurations where two of the three rotation axes align. When the middle rotation reaches that critical value, the first and third rotations act about the same physical direction, so one rotational degree of freedom is lost and the remaining two angles become underdetermined, only their sum or difference is defined. For the \(z\!-\!y\!-\!x\) sequence this happens at \(\beta=\pm 90^\circ\):

\[ R\big|_{\beta=+90^\circ}=\begin{bmatrix}0&0&1\\ \sin(\gamma+\alpha)&\cos(\gamma+\alpha)&0\\ -\cos(\gamma+\alpha)&\sin(\gamma+\alpha)&0\end{bmatrix}, \]

where only \(\gamma+\alpha\) survives. Analytically the map from angles to orientation is rank-deficient there: the Jacobian relating angle rates to angular velocity becomes singular, so a finite, well-behaved motion of the body demands infinite angle rates near the singularity. Mechanically this is the same phenomenon as a physical three-gimbal mount whose inner and outer rings become coplanar and can no longer supply an axis.

## Where it matters and how it is avoided

Gimbal lock is not a bug to be patched but a topological fact: no minimal three-parameter attitude representation can cover all of \(SO(3)\) without a singularity. It bites in orientation control, spacecraft and camera attitude, and inverse kinematics near stretched-out configurations, where a controller can stall or thrash as it approaches the singular pitch. The standard remedies keep the storage and integration in a singularity-free representation, unit quaternions or a rotation matrix, and convert to Euler angles only at the interface where a human reads or specifies them. Even then the convention must be pinned down, because the conversion back from a matrix to angles is genuinely ambiguous exactly on the gimbal-lock set.
