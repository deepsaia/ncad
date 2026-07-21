Contact is how bodies that are not permanently joined push on one another: an end stop arresting a slider, a cam pressing a follower, a part dropping onto a fixture, backlash closing in a gear mesh. Modeling it means answering two questions at each instant: how hard do the surfaces push apart along the normal, and how much do they resist sliding along the tangent. There are two broad approaches. **Non-smooth (complementarity) methods** treat contact as a strict unilateral constraint, allowing no penetration and solving a linear complementarity problem for impulsive reactions. **Regularized (penalty) methods** allow a small, physically interpretable penetration and compute a smooth force from it. Simple contact models, the scope here, use the penalty approach with primitive geometry.

## Normal contact force

Let \(\delta\) be the penetration depth (the overlap of the two surfaces) and \(\dot\delta\) its rate. A general continuous normal-force model is

\[
f_n = k\,\delta^{\,n} + c\,\dot\delta,
\]

where \(k\) is a contact stiffness, \(n\) an exponent (\(n=1\) gives the linear Kelvin-Voigt spring-damper; \(n=\tfrac{3}{2}\) recovers Hertzian sphere contact), and \(c\) a damping term. The Kelvin-Voigt form has a well-known defect: at separation, when \(\delta \to 0\) but \(\dot\delta < 0\), it predicts an unphysical *tensile* (pulling) force. The **Hunt-Crossley** model repairs this by making the damping proportional to penetration,

\[
f_n = k\,\delta^{\,n} + \chi\,\delta^{\,n}\,\dot\delta, \qquad \chi = \frac{3k\,(1 - e^2)}{4\,\dot\delta^{(-)}},
\]

so the force vanishes smoothly at contact onset and release, and the hysteresis damping factor \(\chi\) is tied directly to the coefficient of restitution \(e\) and the impact velocity \(\dot\delta^{(-)}\). The coefficient of restitution \(e \in [0,1]\) sets how much kinetic energy survives an impact (\(e=1\) perfectly elastic, \(e=0\) fully plastic).

## Friction along the tangent

Tangential resistance is captured by the Coulomb model, which caps the friction force by the normal force through a friction coefficient \(\mu\):

\[
\lVert\mathbf{f}_t\rVert \le \mu\,f_n .
\]

While sliding, the friction acts opposite the tangential relative velocity \(\mathbf{v}_t\) at full magnitude, \(\mathbf{f}_t = -\mu\,f_n\,\mathbf{v}_t/\lVert\mathbf{v}_t\rVert\). The ideal law is discontinuous at \(\mathbf{v}_t = 0\) (the stick/slip boundary), which is hostile to time integration, so simple models **regularize** it: the friction coefficient is ramped smoothly through a small velocity threshold \(v_d\), turning the switch into a steep but continuous curve. This trades exact static friction (true sticking) for numerical robustness, which is the accepted compromise at the "simple" tier.

The boundary of what "simple" covers is deliberate. It handles point or sphere-on-plane primitives, a single contact point at a time, regularized (velocity-based) friction, and restitution-based energy loss. It does not attempt full continuous surface-to-surface contact, distributed pressure patches, or exact stick-slip via complementarity, which require heavier non-smooth solvers. Even so, the simple tier covers a large share of practical cases: end stops and travel limits, backlash and clearance, cam-follower and gear-tooth approximations, and drop or impact events. The chief practical caution is numerical stiffness. A high contact stiffness \(k\) produces very fast dynamics that demand small time steps or robust event detection, so contact stiffness and step size must be chosen together.
