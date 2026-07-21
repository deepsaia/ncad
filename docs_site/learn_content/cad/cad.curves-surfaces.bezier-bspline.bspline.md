A B-spline curve generalizes the Bezier curve into a *piecewise* polynomial while keeping a single smooth definition. It is
\[ \mathbf{c}(u) = \sum_{i=0}^{n} N_{i,p}(u)\,\mathbf{P}_i, \]
where \(p\) is the degree, \(\mathbf{P}_i\) are control points, and the \(N_{i,p}\) are the *B-spline basis functions*. The decisive advantage over a single Bezier segment is that the polynomial degree is *decoupled* from the number of control points: a complex curve can have hundreds of control points yet stay cubic (\(p=3\)), avoiding the oscillation and ill-conditioning of high-degree polynomials.

## The knot vector

The extra ingredient is the *knot vector*, a non-decreasing sequence \(U = \{u_0, u_1, \dots, u_m\}\) with \(m = n + p + 1\). Knots partition the parameter domain into spans, and within each span the curve is an ordinary polynomial; at knots the pieces join. The basis functions are defined by the *Cox-de Boor recursion*:
\[ N_{i,0}(u) = \begin{cases} 1 & u_i \le u < u_{i+1} \\ 0 & \text{otherwise} \end{cases} \]
\[ N_{i,p}(u) = \frac{u - u_i}{u_{i+p} - u_i}\,N_{i,p-1}(u) + \frac{u_{i+p+1} - u}{u_{i+p+1} - u_{i+1}}\,N_{i+1,p-1}(u). \]
Each basis function \(N_{i,p}\) is non-negative, the functions sum to one, and crucially each has *local support*: \(N_{i,p}\) is non-zero only on \([u_i, u_{i+p+1})\). That locality is what gives B-splines *local control* - moving one control point changes only \(p+1\) spans of the curve, not the whole thing - which is exactly what a designer expects when editing.

Knot placement and multiplicity are the design levers. *Uniform* knots give translated copies of one basis shape; *non-uniform* knots let the parameterization stretch and compress. Repeating a knot lowers smoothness: at an interior knot of multiplicity \(k\) the curve is only \(C^{p-k}\) continuous, so multiplicity \(p\) forces a sharp corner (a kink) on purpose. A *clamped* (open) knot vector repeats the first and last knots \(p+1\) times, which forces the curve to interpolate its end control points and be tangent to the end legs, mirroring the endpoint behavior of a Bezier curve. Evaluation uses the de Boor algorithm, the B-spline analogue of de Casteljau: a stable pyramid of convex combinations restricted to the \(p+1\) control points active in the span containing \(u\).
