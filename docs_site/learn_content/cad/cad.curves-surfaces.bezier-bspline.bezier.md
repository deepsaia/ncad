A Bezier curve is a polynomial curve defined as a weighted blend of *control points* \(\mathbf{P}_0,\dots,\mathbf{P}_n\), where the weights are the Bernstein basis polynomials:
\[ \mathbf{c}(u) = \sum_{i=0}^{n} B_{i,n}(u)\,\mathbf{P}_i, \qquad B_{i,n}(u) = \binom{n}{i} u^i (1-u)^{n-i}, \quad u \in [0,1]. \]
The control points form a *control polygon* that the designer manipulates; the curve is a smooth, tamed version of that polygon. This shifted the practice of curve design away from fitting coefficients and toward *shaping by handles*, which is why the Bezier form became the foundation of computer-aided geometric design and of vector graphics.

## Properties that make it usable

The Bernstein polynomials are non-negative and sum to one (a *partition of unity*) on \([0,1]\). Three consequences follow directly. First, the curve lies inside the *convex hull* of its control points, which bounds it and accelerates intersection and clipping. Second, the curve is *affinely invariant*: transforming the control points and then evaluating equals evaluating and then transforming. Third, the curve *interpolates its endpoints* (\(\mathbf{c}(0)=\mathbf{P}_0\), \(\mathbf{c}(1)=\mathbf{P}_n\)) and is tangent to the first and last legs of the polygon, so end position and end slope are set explicitly. The basis is also *variation diminishing*: the curve crosses any line no more often than the polygon does, so it does not wiggle more than its handles.

Evaluation uses the *de Casteljau algorithm*, a pyramid of repeated linear interpolations
\[ \mathbf{P}_i^{(r)}(u) = (1-u)\,\mathbf{P}_i^{(r-1)}(u) + u\,\mathbf{P}_{i+1}^{(r-1)}(u), \]
whose apex \(\mathbf{P}_0^{(n)}(u)\) is the point on the curve. Because every step is a convex combination, the scheme is numerically stable and simultaneously *subdivides* the curve into two Bezier pieces, which is the basis of adaptive rendering and intersection. The derivative of a degree-\(n\) Bezier is a degree-\((n-1)\) Bezier on the *difference* control points \(n(\mathbf{P}_{i+1}-\mathbf{P}_i)\).

The defining weakness of a single Bezier segment is that control is *global* and *degree is tied to control-point count*: adding detail raises the polynomial degree, and moving any control point perturbs the whole curve. High-degree polynomials oscillate and are ill-conditioned, so complex shapes are instead built from many low-degree Bezier segments joined with continuity conditions, or, more generally, from B-splines, which retain the Bezier virtues while decoupling degree from the number of control points.
