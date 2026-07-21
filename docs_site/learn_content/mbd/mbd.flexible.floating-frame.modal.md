The floating-frame-of-reference (FFR) formulation is the workhorse method for embedding *flexible* bodies inside a multibody system when the elastic deformations stay small but the body as a whole undergoes large overall motion. Each flexible body carries a body-attached "floating" frame that tracks its gross translation and rotation, and the elastic deformation is measured *relative to that frame*. The global position of a material point \(P\) is therefore the superposition of a large rigid motion and a small elastic field:

\[ \mathbf{r}^{P} = \mathbf{R} + \mathbf{A}\left(\bar{\mathbf{u}}_{0} + \bar{\mathbf{u}}_{f}\right) \]

where \(\mathbf{R}\) locates the frame origin in the inertial system, \(\mathbf{A}(\boldsymbol{\theta})\) is the frame's rotation matrix, \(\bar{\mathbf{u}}_{0}\) is the point's position in the undeformed body, and \(\bar{\mathbf{u}}_{f}\) is its elastic displacement expressed in the body frame.

<svg viewBox="0 0 320 200" width="320" height="200" stroke="currentColor" fill="none" stroke-width="1.5" font-size="11">
  <line x1="20" y1="180" x2="70" y2="180"/>
  <line x1="20" y1="180" x2="20" y2="130"/>
  <text x="72" y="184" stroke="none" fill="currentColor">X</text>
  <text x="10" y="128" stroke="none" fill="currentColor">Y</text>
  <text x="6" y="193" stroke="none" fill="currentColor">O</text>
  <line x1="20" y1="180" x2="150" y2="90" stroke-dasharray="4 3"/>
  <text x="78" y="128" stroke="none" fill="currentColor">R</text>
  <line x1="150" y1="90" x2="196" y2="80"/>
  <line x1="150" y1="90" x2="140" y2="44"/>
  <text x="199" y="81" stroke="none" fill="currentColor">x</text>
  <text x="127" y="43" stroke="none" fill="currentColor">y</text>
  <path d="M150 90 L252 68" stroke-dasharray="4 3"/>
  <path d="M150 90 Q212 94 256 52"/>
  <line x1="252" y1="68" x2="256" y2="52"/>
  <text x="260" y="58" stroke="none" fill="currentColor">u_f</text>
  <text x="196" y="112" stroke="none" fill="currentColor">undeformed</text>
</svg>

## Modal reduction

A full finite-element mesh would make \(\bar{\mathbf{u}}_{f}\) enormous, so FFR projects the deformation onto a small precomputed basis of mode shapes (a Ritz/Galerkin reduction):

\[ \bar{\mathbf{u}}_{f} = \mathbf{S}(\bar{\mathbf{x}})\,\mathbf{q}_{f} \]

Here \(\mathbf{S}\) collects the retained shape vectors as columns and \(\mathbf{q}_{f}\) are the generalized *elastic* coordinates. Choosing \(\mathbf{S}\) well is the crux of the method. Component Mode Synthesis, and specifically the Craig-Bampton scheme, combines fixed-interface normal modes with static constraint modes so that the joint and loading interfaces are represented exactly while the interior is compressed to a handful of degrees of freedom. The body's generalized coordinates then become \(\mathbf{q} = [\mathbf{R},\, \boldsymbol{\theta},\, \mathbf{q}_{f}]\), typically tens of unknowns instead of the thousands in the parent FE model.

## Equations of motion and inertia coupling

Because \(\mathbf{A}\) rotates with the body, the kinetic energy couples the rigid and elastic coordinates nonlinearly. The mass matrix \(\mathbf{M}(\mathbf{q})\) depends on \(\mathbf{q}_{f}\) through a set of precomputed "inertia shape integrals," whereas the elastic stiffness \(\mathbf{K}\) is constant in the body frame. This *variable-mass, constant-stiffness* structure is the signature of FFR. The constrained equations of motion read

\[ \mathbf{M}(\mathbf{q})\,\ddot{\mathbf{q}} + \mathbf{C}_{\mathbf{q}}^{\mathsf{T}}\boldsymbol{\lambda} + \mathbf{K}\mathbf{q} = \mathbf{Q}_{e} + \mathbf{Q}_{v} \]

with \(\mathbf{C}_{\mathbf{q}}\) the constraint Jacobian, \(\boldsymbol{\lambda}\) the Lagrange multipliers enforcing the joints, \(\mathbf{Q}_{e}\) the applied generalized forces, and \(\mathbf{Q}_{v}\) the quadratic-velocity vector carrying the Coriolis, centrifugal, and gyroscopic terms that arise when \(\mathbf{M}(\mathbf{q})\) is differentiated in time.

## Reference conditions and validity

The floating frame is redundant with the six rigid-body modes latent in the deformation field, so one imposes *reference conditions* to make the split unique. Fixed (cantilever) conditions clamp the frame to a node; mean-axis (Buckens) conditions instead require the deformation to carry zero net linear and angular momentum relative to the frame, which minimizes the elastic kinetic energy and gives the cleanest modal set for free-floating bodies such as spacecraft appendages. FFR is accurate only while \(\bar{\mathbf{u}}_{f}\) remains small relative to the body frame: the frame absorbs the large rotation, so the modest bending of a slender arm is fine but large elastic strains are not. When deformations become geometrically large (belts, cables, tires), a non-incremental large-deformation formulation is needed instead. FFR is standard for rotating blades, robotic manipulators, vehicle suspension links, and deployable structures, where flexibility measurably shifts natural frequencies, injects vibration, and couples back into the rigid-body dynamics.
