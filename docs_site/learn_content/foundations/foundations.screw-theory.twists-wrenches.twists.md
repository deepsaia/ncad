A **twist** is the six-dimensional description of the *instantaneous velocity* of a rigid body. Because a free rigid body has six degrees of freedom, its complete state of motion at an instant cannot be captured by a single 3-vector: it needs three numbers for how fast it is spinning and three for how fast a reference point is translating. A twist packs both into one object, conventionally written angular-part-first as

\[
\mathcal{V} = \begin{bmatrix} \omega \\ v \end{bmatrix} \in \mathbb{R}^6,
\]

where \(\omega\) is the angular velocity and \(v\) is the linear velocity of the body-fixed point that instantaneously coincides with the origin of the reference frame. The subtlety in that last clause is essential: \(v\) is **not** the velocity of the body's centroid or of any physical material point in general, but the velocity of the imaginary extended point at the origin. This convention is what makes twists transform cleanly and compose by simple addition.

## The screw interpretation

The deep content of screw theory is **Chasles' theorem**: every instantaneous rigid-body motion is equivalent to a rotation about some unique axis in space combined with a translation along that same axis, exactly like the motion of a nut on a bolt. That axis-plus-pitch object is the *screw*, and a twist is a screw scaled by a rate. Writing the unit screw axis as \(\mathcal{S}=(\omega, v)\) with \(\|\omega\|=1\) (or, for a pure translation, \(\omega=0,\ \|v\|=1\)), any twist factors as \(\mathcal{V} = \mathcal{S}\,\dot\theta\), where \(\dot\theta\) is the scalar speed along the screw. The **pitch** \(h = \omega^\top v / \|\omega\|^2\) is the ratio of translation to rotation; \(h=0\) is a pure rotation and \(h=\infty\) a pure translation.

## Matrix form and the two frames

A twist has a matrix representation in the Lie algebra \(\mathfrak{se}(3)\),

\[
[\mathcal{V}] = \begin{bmatrix} [\omega] & v \\ 0 & 0 \end{bmatrix},\qquad [\omega]=\begin{bmatrix} 0 & -\omega_3 & \omega_2 \\ \omega_3 & 0 & -\omega_1 \\ -\omega_2 & \omega_1 & 0 \end{bmatrix},
\]

where \([\omega]\) is the skew-symmetric (cross-product) matrix. If \(T(t)\in SE(3)\) is the body's pose, then \(\dot T T^{-1} = [\mathcal{V}_s]\) yields the **spatial (fixed-frame) twist**, while \(T^{-1}\dot T = [\mathcal{V}_b]\) yields the **body-frame twist**. The two are related by the adjoint map, \(\mathcal{V}_s = [\mathrm{Ad}_T]\,\mathcal{V}_b\), a \(6\times 6\) transformation built from the rotation and translation of \(T\). Choosing the right frame is what keeps velocity and Jacobian expressions compact.

Twists matter wherever instantaneous kinematics drives an analysis: robot and mechanism Jacobians are matrices whose columns are joint screw axes, so end-effector velocity is a linear combination of joint twists. Velocity-level inverse kinematics, singularity detection (where twist columns become linearly dependent), contact and grasp constraints, and the propagation of link velocities through a kinematic chain are all naturally and coordinate-independently expressed through twists.

<svg viewBox="0 0 260 120" width="260" height="120" stroke="currentColor" fill="none" stroke-width="1.5">
  <line x1="20" y1="90" x2="230" y2="30"/>
  <path d="M180 34 a26 26 0 1 1 -14 22" stroke-dasharray="4 3"/>
  <polygon points="166,56 160,50 172,49" fill="currentColor"/>
  <line x1="205" y1="38" x2="235" y2="29"/>
  <polygon points="235,29 227,28 230,35" fill="currentColor"/>
  <text x="30" y="105" font-size="11" stroke="none" fill="currentColor">screw axis (direction ω)</text>
  <text x="192" y="20" font-size="11" stroke="none" fill="currentColor">translate</text>
</svg>
