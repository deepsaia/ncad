The Newton-Euler equations state the two independent balance laws that govern a single rigid body: linear momentum responds to net force, and angular momentum responds to net moment. Writing the body mass as \(m\), the acceleration of its mass center as \(\mathbf{a}_C\), the net external force as \(\sum\mathbf{F}\), and the net moment about the mass center as \(\sum\mathbf{M}_C\), the pair reads

\[ \sum\mathbf{F} = m\,\mathbf{a}_C, \qquad \sum\mathbf{M}_C = \mathbf{I}_C\,\boldsymbol{\alpha} + \boldsymbol{\omega}\times(\mathbf{I}_C\,\boldsymbol{\omega}). \]

The first line is Newton's second law; the second is Euler's rotational equation. Here \(\boldsymbol{\omega}\) and \(\boldsymbol{\alpha}\) are the body angular velocity and angular acceleration, and \(\mathbf{I}_C\) is the inertia tensor taken about the mass center. The term \(\boldsymbol{\omega}\times(\mathbf{I}_C\boldsymbol{\omega})\) is the gyroscopic coupling: it appears because the angular momentum \(\mathbf{I}_C\boldsymbol{\omega}\) is generally not parallel to \(\boldsymbol{\omega}\), and it is what makes a spinning body precess even under zero applied moment.

<svg viewBox="0 0 260 130" width="260" height="130" stroke="currentColor" fill="none" stroke-width="1.5"><rect x="70" y="40" width="90" height="55" rx="8"/><circle cx="115" cy="67" r="3" fill="currentColor"/><text x="120" y="63" font-size="11" stroke="none" fill="currentColor">C</text><line x1="115" y1="67" x2="215" y2="30"/><polygon points="215,30 205,30 210,38" fill="currentColor" stroke="none"/><text x="200" y="22" font-size="12" stroke="none" fill="currentColor">F</text><path d="M 60 55 A 22 22 0 1 0 60 80"/><polygon points="60,80 52,74 68,72" fill="currentColor" stroke="none"/><text x="18" y="70" font-size="12" stroke="none" fill="currentColor">M</text></svg>

## Body frame and the choice of reference point

The rotational equation is cleanest when expressed in a body-fixed frame, because there the inertia tensor is constant. If that frame is aligned with the principal axes of inertia, \(\mathbf{I}_C = \mathrm{diag}(I_1,I_2,I_3)\) and Euler's equation separates into the classical scalar form

\[ \begin{aligned} M_1 &= I_1\dot\omega_1 + (I_3-I_2)\,\omega_2\omega_3,\\ M_2 &= I_2\dot\omega_2 + (I_1-I_3)\,\omega_3\omega_1,\\ M_3 &= I_3\dot\omega_3 + (I_2-I_1)\,\omega_1\omega_2. \end{aligned} \]

The reference point matters: the compact moment equation above holds about the mass center or about a point that is fixed in an inertial frame. Taking moments about an arbitrary accelerating point introduces an extra transport term \(\mathbf{r}_{C/P}\times m\,\mathbf{a}_P\), which is a frequent source of sign and bookkeeping errors.

## Spatial form and multibody recursion

For multibody systems the two balances are often stacked into a single six-dimensional spatial equation, \(\mathbf{f} = \mathbf{I}\,\dot{\mathbf{v}} + \mathbf{v}\times^{*}\mathbf{I}\,\mathbf{v}\), where \(\mathbf{v}\) is the spatial (twist) velocity, \(\mathbf{f}\) is the spatial force (wrench), and \(\mathbf{I}\) is the \(6\times6\) spatial inertia. Written this way, the equations for a chain of jointed bodies are evaluated by the recursive Newton-Euler algorithm: an outward pass propagates velocities and accelerations from the base to the leaves, and an inward pass accumulates the interbody forces from the leaves back to the base. This yields joint forces or torques in \(O(n)\) operations for an \(n\)-body chain.

Because it is a direct force-and-torque accounting, the Newton-Euler form is the natural language of inverse dynamics (given motion, find the actuator loads) and of contact and joint-reaction analysis, where the internal constraint forces are themselves the quantities of interest. Its trade-off relative to energy-based formulations is that every constraint and reaction force appears explicitly, so a system with many joints requires either careful elimination of those unknowns or a companion constraint formulation to close the system.
