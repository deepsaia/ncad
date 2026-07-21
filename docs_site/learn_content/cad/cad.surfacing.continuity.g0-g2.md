Continuity describes how smoothly two curves or surfaces meet along a shared boundary, and it is graded by how many orders of geometric information match across the join. The three engineering-relevant levels are \(G^0\) (positional: the pieces touch), \(G^1\) (tangent: they share a common tangent plane, so the surface normal is continuous), and \(G^2\) (curvature: the normal curvature agrees for every direction along the seam). Geometric continuity \(G^n\) is deliberately distinguished from parametric continuity \(C^n\): \(C^n\) requires the parametric derivatives themselves to be equal, whereas \(G^n\) only requires them to agree after an allowable reparameterization. A curve can be \(G^1\) yet not \(C^1\) when the tangent directions align but the speeds differ, which is why continuity for shape must be defined geometrically rather than through raw derivatives.

For two curve segments \(\mathbf{r}_1,\mathbf{r}_2\) joined end to end, the geometric conditions are captured compactly by the beta constraints. \(G^1\) requires the incoming and outgoing tangents to be parallel and same-sense,

\[
\mathbf{r}_2'(0) = \beta_1\,\mathbf{r}_1'(1),\qquad \beta_1 > 0,
\]

and \(G^2\) adds a matching condition on the second derivative that guarantees the curvature vectors coincide,

\[
\mathbf{r}_2''(0) = \beta_1^{\,2}\,\mathbf{r}_1''(1) + \beta_2\,\mathbf{r}_1'(1),
\]

where \(\beta_1\) (a scale) and \(\beta_2\) (a bias) are the shape parameters that make the constraints independent of parameterization.

For surfaces the same hierarchy applies along the shared boundary curve. \(G^0\) means the two trimmed edges are geometrically identical. \(G^1\) means the tangent planes coincide all along the seam, equivalently the cross-boundary derivative of each surface lies in the other's tangent plane and the unit normals match. \(G^2\) means the surfaces share the same normal curvature in every direction at every seam point, which is a condition on the second fundamental form along the boundary. In a control-point representation these conditions are imposed by constraining the first (for \(G^1\)) and second (for \(G^2\)) rows of control points adjacent to the seam of one surface to specific combinations of the other's, so the match holds exactly rather than approximately.

The order chosen has real physical consequences. A \(G^0\) seam is a visible crease and a stress concentrator; a \(G^1\) seam has a continuous normal but a jump in curvature that shows up as a bright line under reflection and as a witness mark or tool-path discontinuity in machining and molding; \(G^2\) removes the curvature jump and is the practical target for surfaces where reflections and flow quality matter. Many mainstream modeling kernels treat \(G^2\) as their achievable ceiling for robust surface matching, which is why engineering surfacing specifications are usually written in terms of \(G^0/G^1/G^2\).
