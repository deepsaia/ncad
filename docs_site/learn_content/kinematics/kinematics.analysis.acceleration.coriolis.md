## Second-order kinematics

Acceleration analysis is the natural continuation of velocity analysis: once positions and velocities are known, differentiating the velocity relations once more gives the accelerations needed for dynamics (through \(\mathbf{F} = m\mathbf{a}\) and the equivalent for rotation) and for smooth-motion design. For a rigid body in general motion, the acceleration of a point \(P\) fixed on it, relative to a reference point \(O\) on the same body, is

\[ \mathbf{a}_P = \mathbf{a}_O + \boldsymbol{\alpha}\times\mathbf{r} + \boldsymbol{\omega}\times(\boldsymbol{\omega}\times\mathbf{r}), \]

where \(\mathbf{r} = \mathbf{r}_{P/O}\), \(\boldsymbol{\omega}\) is the angular velocity, and \(\boldsymbol{\alpha}\) the angular acceleration. The term \(\boldsymbol{\alpha}\times\mathbf{r}\) is the **tangential** acceleration and \(\boldsymbol{\omega}\times(\boldsymbol{\omega}\times\mathbf{r})\) is the **centripetal** (normal) acceleration, of magnitude \(\omega^2 r\) directed toward \(O\). For a body pinned to ground these two terms fully describe the acceleration field.

## The moving-frame formula and the Coriolis term

The extra subtlety appears when a point also moves *relative to* a body that is itself rotating, as at a sliding joint (a block on a spinning link, a follower in a rotating slot, a piston in a swinging cylinder). Let \(B\) be a point coincident with \(P\) but fixed to the rotating body, whose frame turns at \(\boldsymbol{\omega}\) and \(\boldsymbol{\alpha}\), and let \(\mathbf{v}_{\text{rel}}\), \(\mathbf{a}_{\text{rel}}\) be the velocity and acceleration of \(P\) measured within that frame. The full acceleration is the five-term relation

\[ \mathbf{a}_P = \mathbf{a}_{B} + \mathbf{a}_{\text{rel}} + 2\,\boldsymbol{\omega}\times\mathbf{v}_{\text{rel}}, \]

in which \(\mathbf{a}_B = \mathbf{a}_{O} + \boldsymbol{\alpha}\times\mathbf{r} + \boldsymbol{\omega}\times(\boldsymbol{\omega}\times\mathbf{r})\) is the transport acceleration and

\[ \mathbf{a}_{\text{cor}} = 2\,\boldsymbol{\omega}\times\mathbf{v}_{\text{rel}} \]

is the **Coriolis acceleration**. It has no counterpart in the rigid-point case and is easy to omit by mistake: it exists only when a body both rotates and lets a point slide along it, and it is directed perpendicular to the relative sliding velocity. Its magnitude \(2\,\omega\,v_{\text{rel}}\) is often the dominant, and most surprising, contribution in slotted-lever and quick-return mechanisms.

## Formulating and solving the equations

For a full mechanism, acceleration analysis is obtained by differentiating the loop-closure constraints \(\boldsymbol{\Phi}(\mathbf{q}) = \mathbf{0}\) twice with respect to time. The first derivative gives the velocity relation \(\boldsymbol{\Phi}_{\mathbf{q}}\dot{\mathbf{q}} = \mathbf{0}\); differentiating again gives

\[ \boldsymbol{\Phi}_{\mathbf{q}}\,\ddot{\mathbf{q}} = -\,\dot{\boldsymbol{\Phi}}_{\mathbf{q}}\,\dot{\mathbf{q}} \;\equiv\; \boldsymbol{\gamma}(\mathbf{q},\dot{\mathbf{q}}), \]

which is **linear** in the unknown accelerations \(\ddot{\mathbf{q}}\) even though the position problem was nonlinear. The right-hand side \(\boldsymbol{\gamma}\), which gathers the products of known velocities, is exactly where the centripetal and Coriolis contributions live. This is why acceleration analysis, unlike position analysis, needs only one linear solve per step once the same constraint Jacobian \(\boldsymbol{\Phi}_{\mathbf{q}}\) has been factored.

## Where it matters

The same structure carries into rigid-body dynamics. In the manipulator equations of motion,

\[ \mathbf{M}(\mathbf{q})\,\ddot{\mathbf{q}} + \mathbf{C}(\mathbf{q},\dot{\mathbf{q}})\,\dot{\mathbf{q}} + \mathbf{g}(\mathbf{q}) = \boldsymbol{\tau}, \]

the matrix \(\mathbf{C}\) collects precisely the Coriolis and centrifugal (velocity-product) terms, quadratic in \(\dot{\mathbf{q}}\), that this analysis produces. Accurate acceleration analysis therefore drives inertial-force and bearing-load calculation, balancing and vibration studies, cam and follower design, and the feed-forward torques of model-based motion control. Neglecting the Coriolis component in any mechanism with a rotating sliding joint is a classic source of large, systematic error.
