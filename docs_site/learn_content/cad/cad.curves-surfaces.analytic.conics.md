The conic sections - ellipse, parabola, and hyperbola (with the circle as a special ellipse) - are the curves obtained by slicing a cone with a plane, and equivalently the zero set of a general quadratic
\[ a x^2 + b xy + c y^2 + d x + e y + f = 0. \]
The implicit form is compact but poorly suited to interactive design: it is hard to see the shape from the coefficients, and a bounded arc must be carved out by extra inequalities. CAD systems therefore favor a *constructive* description of a conic segment built from geometry a designer can grab directly: the two endpoints \(P_0\) and \(P_2\), the *apex* \(P_1\) where the two end tangents intersect, and a single scalar shape parameter.

## The rational-quadratic (rho) model

Every bounded conic arc is exactly a *rational quadratic Bezier* curve. With unit weights at the endpoints and a single interior weight \(w\) on the apex,
\[ \mathbf{c}(u) = \frac{(1-u)^2\,P_0 + 2u(1-u)\,w\,P_1 + u^2\,P_2}{(1-u)^2 + 2u(1-u)\,w + u^2}, \qquad u\in[0,1]. \]
The interior weight selects the conic type through the discriminant of the denominator: \(w<1\) gives an ellipse, \(w=1\) a parabola, and \(w>1\) a hyperbola. Because raw weights are unbounded and unintuitive, kernels reparameterize by the *projective discriminant*, or **rho** value,
\[ \rho = \frac{w}{1+w} \in (0,1). \]
Evaluating the curve at its midpoint shows what rho means geometrically. Let \(M = \tfrac{1}{2}(P_0+P_2)\) be the chord midpoint; then
\[ \mathbf{c}(\tfrac12) = (1-\rho)\,M + \rho\,P_1, \]
so the *shoulder point* sits a fraction rho of the way along the median from the chord midpoint toward the apex. \(\rho=\tfrac12\) (equivalently \(w=1\)) is the parabola; \(\rho<\tfrac12\) is elliptic and \(\rho>\tfrac12\) is hyperbolic.

This endpoint-plus-apex-plus-rho parameterization is the representation used by the major exchange standards and by professional modelers precisely because it is both robust and designer-facing: dragging the shoulder point continuously morphs the arc through the whole conic family while endpoints and end tangents stay pinned. It also converts trivially to and from the rational-Bezier weight form, so the same evaluator that handles NURBS handles conics with no special case, and the analytic classification (which conic, what eccentricity) is recoverable when downstream reasoning needs it.
