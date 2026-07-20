A **homogeneous transformation matrix** packs a rotation and a translation into a single
$4\times4$ matrix that acts on points written in homogeneous coordinates $(x, y, z, 1)$:

\[
T = \begin{bmatrix} R & t \\ 0\ 0\ 0 & 1 \end{bmatrix},
\qquad
\begin{bmatrix} v' \\ 1 \end{bmatrix} = T \begin{bmatrix} v \\ 1 \end{bmatrix}.
\]

Here $R \in SO(3)$ is the $3\times3$ rotation and $t$ is the translation. The bottom row $(0\,0\,0\,
1)$ makes the matrix act as an affine map, rotate-then-translate, in one multiplication. The set of
such matrices is the **special Euclidean group** $SE(3)$, the group of rigid-body motions.

## Why one matrix for both

Combining rotation and translation into one operator is what makes transform chains composable. A
part placed on a subassembly placed on an assembly is the product $T_\text{asm} T_\text{sub}
T_\text{part}$, evaluated once per point. The inverse has a closed form,

\[
T^{-1} = \begin{bmatrix} R^\top & -R^\top t \\ 0\ 0\ 0 & 1 \end{bmatrix},
\]

so moving a coordinate from world frame to a local frame is as cheap as the forward direction. This
is the algebra behind assembly placement, connector/mate frames, and feature coordinate systems:
every "put this frame on that frame" is a homogeneous-matrix composition.

## Points versus directions

The homogeneous coordinate distinguishes points from directions: a point is $(x, y, z, 1)$ and is
affected by translation, while a direction or free vector is $(x, y, z, 0)$ and is rotated but not
translated. Getting this fourth coordinate right is what keeps normals and axes correct under a
transform that includes translation.
