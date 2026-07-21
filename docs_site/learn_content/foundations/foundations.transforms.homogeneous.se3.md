A **rigid-body motion** is a displacement that preserves all distances and handedness: it may rotate and translate a body but never stretch, shear, or mirror it. The set of all such motions in three dimensions forms the **special Euclidean group** \(SE(3)\), the mathematical home of every pose, placement, joint, and coordinate-frame relationship in a mechanical model. Its power is that it packages the rotation and the translation into a single object that composes by ordinary matrix multiplication.

## Homogeneous transformation matrices

The standard concrete form of an \(SE(3)\) element is the \(4\times 4\) **homogeneous transformation matrix**

\[ T = \begin{bmatrix} R & p \\ 0\;\;0\;\;0 & 1 \end{bmatrix},\qquad R\in SO(3),\; p\in\mathbb{R}^3. \]

Points are carried as homogeneous vectors \(\tilde{p}=(x,y,z,1)^{\mathsf T}\), and a pose acts by \(\tilde{p}' = T\,\tilde{p}\), which applies the rotation and then adds the translation in one step. The extra row and column are the algebraic trick that turns an *affine* map (rotation plus offset) into a purely *linear* one in a higher dimension, so that translations, which are not linear on their own, chain by the same matrix product as rotations.

## Group structure: composition and inverse

Composition of two motions is a matrix product, and it inherits the non-commutativity of rotation:

\[ {}^{A}_{C}T = {}^{A}_{B}T\;{}^{B}_{C}T. \]

This is exactly how an assembly tree or a kinematic chain resolves a leaf frame into world coordinates. The inverse has a closed form that avoids any general \(4\times 4\) inversion:

\[ T^{-1} = \begin{bmatrix} R^{\mathsf T} & -R^{\mathsf T}p \\ 0\;\;0\;\;0 & 1 \end{bmatrix}, \]

using the same transpose-is-inverse property of the rotation block. Structurally \(SE(3)\) is the **semidirect product** \(\mathbb{R}^3 \rtimes SO(3)\): translations and rotations are intertwined, not independent, because rotating first changes where a subsequent translation points.

## Twists, screws, and exponential coordinates

\(SE(3)\) is a six-dimensional Lie group, and by **Chasles' theorem** every rigid motion is a screw motion, a rotation about some axis combined with a translation along it. The infinitesimal version, an angular plus linear velocity, is a **twist** \(\mathcal{V}=(\omega,v)\), and finite motions are recovered by the exponential map

\[ T = \exp\!\big([\mathcal{S}]\theta\big),\qquad [\mathcal{S}] = \begin{bmatrix} [\omega] & v \\ 0 & 0 \end{bmatrix} \in \mathfrak{se}(3), \]

where \(\mathcal{S}\) is the screw axis and \(\theta\) the amount of motion along it. These **exponential coordinates** give a singularity-robust way to represent, integrate, and interpolate poses, and the twist formulation is the basis of modern kinematics and multibody dynamics.

In practice \(SE(3)\) is the lingua franca of geometry pipelines: it places instances in an assembly, expresses datum and mounting relationships, defines the pose of every joint frame in a mechanism, and, restricted to its rotation block, reduces to the \(SO(3)\) change-of-basis case. Because the composition and inverse are exact and cheap, deep frame hierarchies stay both correct and numerically stable.
