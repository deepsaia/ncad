The **inertia tensor** is the rotational counterpart of mass: it tells you how a rigid body resists angular acceleration and how its angular momentum relates to its angular velocity. Where a single scalar \(m\) captures resistance to translation, rotation needs a \(3\times3\) symmetric matrix because a body can be easy to spin about one axis and hard to spin about another, and because spinning about one axis can generate momentum about a different axis. It is the second mass property (after mass and center of mass) that every dynamics solver requires, and it is computed directly from the body's geometry and density distribution.

For a body of density \(\rho\) occupying volume \(V\), with position \(\mathbf{r}\) measured from the reference point, the inertia tensor is

\[ \mathbf{I} = \int_V \rho\left(\lVert\mathbf{r}\rVert^2\,\mathbf{1} - \mathbf{r}\,\mathbf{r}^{\top}\right)dV, \]

whose diagonal entries are the **moments of inertia** \(I_{xx}=\int\rho(y^2+z^2)\,dV\) (and cyclic permutations) and whose off-diagonal entries are the negatives of the **products of inertia** \(I_{xy}=\int\rho\,xy\,dV\). The tensor is symmetric and positive definite for any real body, so it has three real positive eigenvalues, the **principal moments of inertia**, with mutually orthogonal eigenvectors, the **principal axes**. Expressed in the principal frame the tensor is diagonal and the products of inertia vanish, which is why body-fixed principal axes are the preferred frame for writing Euler's equation.

## The parallel-axis (Huygens-Steiner) theorem

Inertia depends on the reference point. The **parallel-axis theorem** relates the inertia tensor about the center of mass \(c\) to the inertia tensor about any parallel-axis point \(P\) offset by the vector \(\mathbf{d}\) from \(c\) to \(P\):

\[ \mathbf{I}_P = \mathbf{I}_c + m\left(\lVert\mathbf{d}\rVert^2\,\mathbf{1} - \mathbf{d}\,\mathbf{d}^{\top}\right). \]

For a single axis at perpendicular distance \(d\) this reduces to the familiar scalar form \(I_P = I_c + m d^2\). The theorem always *adds* inertia away from the center of mass, so the center of mass minimizes the moment of inertia among all parallel axes. It is what lets a solver store one canonical tensor per body (about its own center of mass) and shift it to any joint or connection point on demand. Note the theorem only moves the reference point between parallel axes; to change the *orientation* of the frame you rotate the tensor by a similarity transform \(\mathbf{I}' = \mathbf{R}\,\mathbf{I}\,\mathbf{R}^{\top}\), where \(\mathbf{R}\) is the rotation between frames.

<svg viewBox="0 0 320 150" width="320" height="150" stroke="currentColor" fill="none" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="120" cy="80" rx="55" ry="32"/>
  <circle cx="120" cy="80" r="3" fill="currentColor"/>
  <line x1="120" y1="20" x2="120" y2="140" stroke-dasharray="4 3"/>
  <line x1="240" y1="20" x2="240" y2="140" stroke-dasharray="4 3"/>
  <line x1="120" y1="80" x2="240" y2="80"/>
  <text x="175" y="74" font-size="12" fill="currentColor" stroke="none">d</text>
  <text x="104" y="16" font-size="11" fill="currentColor" stroke="none">axis through c</text>
  <text x="210" y="16" font-size="11" fill="currentColor" stroke="none">axis at P</text>
  <text x="126" y="96" font-size="11" fill="currentColor" stroke="none">c</text>
</svg>

## Where it matters

In practice the tensor is obtained by integrating over the solid model: mass-property routines evaluate the volume integrals above from the boundary representation (via the divergence theorem, turning volume integrals into surface integrals), returning mass, center of mass, and the inertia tensor together. Those quantities then populate the mass matrix of the Newton-Euler equations, so any error in geometry or assigned density propagates directly into predicted accelerations, reaction forces, and vibration modes. Getting the inertia tensor right, in the correct frame and about the correct point, is therefore a prerequisite for trustworthy force-driven simulation, balancing analysis, and control design.
