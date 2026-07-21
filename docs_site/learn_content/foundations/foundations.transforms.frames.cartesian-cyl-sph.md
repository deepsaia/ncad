A *coordinate frame* is a rule for attaching numbers to the points of space so that geometry becomes algebra. Every frame fixes an origin and a set of coordinate directions; the numbers we read off are always *relative to that frame*. The three canonical frames of engineering, Cartesian, cylindrical, and spherical, are all **orthogonal**: at every point their coordinate directions meet at right angles. They differ in whether those directions are fixed in space (Cartesian) or vary from point to point (the two curvilinear systems). Choosing the frame that matches a part's symmetry is not cosmetic: it collapses constraints, cleans up integrals, and makes tolerances and meshing natural rather than accidental.

## The three systems

The **Cartesian** frame uses three mutually perpendicular straight axes with a constant, right-handed orthonormal basis \((\hat{e}_x,\hat{e}_y,\hat{e}_z)\). A point is \(p=(x,y,z)\), the basis is the same everywhere, and the distance element is simply \(ds^2 = dx^2+dy^2+dz^2\). This uniformity is why it is the default for storage and for expressing rigid motions.

The **cylindrical** frame \((r,\theta,z)\) wraps the plane into a radius and azimuth while keeping a straight height axis. It is the right language for anything with an axis of revolution: bores, shafts, revolved profiles, pressure vessels, rotating machinery. The conversions are

\[ x = r\cos\theta,\quad y = r\sin\theta,\quad z = z,\qquad r=\sqrt{x^2+y^2},\quad \theta=\operatorname{atan2}(y,x). \]

The **spherical** frame \((\rho,\vartheta,\varphi)\) uses a radius plus two angles and suits spherical shells, radial fields, and antenna or lens geometry. Following the ISO 80000-2 convention (\(\vartheta\) the polar/inclination angle from \(+z\), \(\varphi\) the azimuth in the \(xy\)-plane),

\[ x=\rho\sin\vartheta\cos\varphi,\quad y=\rho\sin\vartheta\sin\varphi,\quad z=\rho\cos\vartheta. \]

Beware that the mathematics literature frequently swaps the names of the two angles; a stated convention is mandatory before any spherical data is exchanged.

## Why curvilinear frames behave differently

In a curvilinear frame the basis vectors are attached to the point, not to space, so \(\hat{e}_r,\hat{e}_\theta\) rotate as you move around the axis. Each coordinate also carries a **scale factor** (Lamé coefficient) that converts a coordinate increment into a physical length: \((h_r,h_\theta,h_z)=(1,r,1)\) for cylindrical and \((h_\rho,h_\vartheta,h_\varphi)=(1,\rho,\rho\sin\vartheta)\) for spherical. These factors are exactly what appear in the volume element \(dV=r\,dr\,d\theta\,dz\) or \(dV=\rho^2\sin\vartheta\,d\rho\,d\vartheta\,d\varphi\), and they reshape the gradient, divergence, and Laplacian. A practical consequence: because the basis is position-dependent, vector *components* in a curvilinear frame cannot be added blindly across different points, and any interchange of data must record which frame and which convention produced the numbers.

<svg viewBox="0 0 260 150" width="260" height="150" stroke="currentColor" fill="none" stroke-width="1.2"><line x1="30" y1="120" x2="30" y2="20"/><line x1="30" y1="120" x2="210" y2="120"/><ellipse cx="30" cy="120" rx="70" ry="20"/><line x1="30" y1="120" x2="92" y2="110" stroke-dasharray="3 2"/><circle cx="92" cy="70" r="3" fill="currentColor"/><line x1="92" y1="110" x2="92" y2="70" stroke-dasharray="3 2"/><text x="58" y="116" font-size="11" stroke="none" fill="currentColor">r</text><text x="96" y="92" font-size="11" stroke="none" fill="currentColor">z</text><text x="40" y="134" font-size="11" stroke="none" fill="currentColor">θ</text><text x="98" y="66" font-size="11" stroke="none" fill="currentColor">P</text></svg>

The governing idea is invariance: the point \(P\) is one physical thing, and the three frames are three descriptions of it linked by exact, invertible maps. Modeling and analysis pick whichever description makes the equations simplest, then convert back to a common Cartesian reference for storage and for combining with rigid-body motions.
