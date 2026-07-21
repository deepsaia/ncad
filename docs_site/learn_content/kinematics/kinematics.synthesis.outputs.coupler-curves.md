When a linkage moves, any point rigidly attached to a moving link traces a curve in the fixed frame. The general term is a **trace curve**; the most studied special case is the **coupler curve**, the path swept by a point fixed to the floating link (the coupler) of a four-bar linkage. Trace and coupler curves are the primary geometric *output* of a mechanism simulation: they are what you inspect to see whether an end effector follows a required contour, whether a marked feature clears an obstacle, or whether a point dwells, reverses, or crosses itself at the right moment.

The coupler point is not on either grounded pivot, so it neither sits still nor moves on a simple circle; it undergoes general planar motion. Its curve is obtained parametrically by driving the input crank and, for each input angle \( \theta_2 \), solving the loop-closure (position) equations for the coupler orientation \( \theta_3 \), then evaluating the point:

\[ \mathbf{r}_2(\theta_2) + \mathbf{r}_3(\theta_3) = \mathbf{r}_1 + \mathbf{r}_4(\theta_4), \qquad \mathbf{P}(\theta_2) = \mathbf{r}_2(\theta_2) + \mathbf{R}\!\left(\theta_3\right)\,\mathbf{p}, \]

where \( \mathbf{p} \) is the coupler point expressed in the coupler's local frame and \( \mathbf{R} \) is the rotation by \( \theta_3 \). Because the loop closure is quadratic (two assembly configurations, the *branches*), a coupler curve generally has two branches, and a simulator must track the correct one continuously to avoid jumping between assemblies mid-cycle.

## Algebraic character and cognates

Eliminating the input parameter shows that the four-bar coupler curve is an algebraic curve of degree six, a **tricircular sextic**: it meets the line at infinity's two circular points three times each. This high degree is what lets a single simple linkage produce remarkably rich shapes, including approximate straight-line segments, near-circular arcs, cusps, and self-intersecting figure-eights with crunodes that create instantaneous dwells. A profound classical result, the **Roberts-Chebyshev cognate theorem**, states that three geometrically distinct four-bar linkages (the three cognates) trace exactly the same coupler curve; this gives the designer alternative mechanisms with different pivot locations, transmission angles, and packaging for one desired path.

<svg viewBox="0 0 260 150" width="260" height="150" stroke="currentColor" fill="none" stroke-width="1.5">
  <circle cx="40" cy="120" r="3"/>
  <circle cx="200" cy="120" r="3"/>
  <line x1="40" y1="120" x2="70" y2="70"/>
  <line x1="70" y1="70" x2="150" y2="55"/>
  <line x1="150" y1="55" x2="200" y2="120"/>
  <circle cx="110" cy="40" r="2.5"/>
  <line x1="70" y1="70" x2="110" y2="40" stroke-dasharray="3 2"/>
  <line x1="150" y1="55" x2="110" y2="40" stroke-dasharray="3 2"/>
  <path d="M110 40 C 150 20 170 60 130 78 C 95 92 60 70 90 48 C 100 40 105 40 110 40 Z" stroke-dasharray="2 2"/>
  <text x="114" y="36" font-size="9" stroke="none" fill="currentColor">P</text>
</svg>

## Using trace curves in practice

Because the coupler curve is only piecewise well behaved, the useful design information lives in its qualitative features: an approximately straight segment (exploited by straight-line linkages such as the Watt, Chebyshev, Hoeken, and Roberts geometries), a segment of near-constant velocity, or a dwell where the point nearly stops. Historically, atlases catalogued thousands of four-bar coupler curves so designers could pick a shape by inspection; today the same curve is generated numerically by sampling the input over its full range and, where a body rather than a point matters, by carrying the pose forward to produce swept regions. Trace curves are also the raw material for downstream measures (velocity and acceleration along the path) and for clearance and interference checks against neighboring geometry.
