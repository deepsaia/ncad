An *offset surface* is the locus of points a fixed signed distance \(d\) from a base surface \(\mathbf{S}(u,v)\), measured along the surface normal:
\[ \mathbf{S}_d(u,v) = \mathbf{S}(u,v) + d\,\mathbf{n}(u,v), \qquad \mathbf{n}(u,v) = \frac{\mathbf{S}_u \times \mathbf{S}_v}{\lVert \mathbf{S}_u \times \mathbf{S}_v \rVert}. \]
Offsets are ubiquitous: shelling a solid to a uniform wall thickness, generating clearance envelopes, and above all computing machining tool paths, where the cutter-contact surface is offset by the tool radius to obtain the cutter-center surface. The operation looks trivial but is one of the genuinely hard problems in geometric modeling, for two connected reasons.

## Why offsets are not closed and not free

First, the offset of a NURBS surface is *generally not a NURBS surface*. The normal field contains the normalization \(1/\lVert \mathbf{S}_u \times \mathbf{S}_v \rVert\), a square root of a polynomial, which is not a rational function; only special cases (planes, circles, spheres, and a few others) offset exactly. In practice the true offset is *approximated* by a NURBS within a stated tolerance, so offset quality is a fit problem and the result's control-point count grows with the required accuracy and the base surface's curvature variation.

Second, offsetting past a critical distance produces *self-intersection*. Under offsetting, the principal curvatures transform as
\[ \kappa_i^{\text{off}} = \frac{\kappa_i}{1 + d\,\kappa_i}, \qquad i = 1,2, \]
which blows up when \(1 + d\,\kappa_i = 0\), i.e. when the offset distance equals a *principal radius of curvature* on the concave side (\(d = -1/\kappa_i\)). At and beyond that distance the offset develops *local* self-intersections (cusps and swallowtails); separately, remote parts of the surface can collide, producing *global* self-intersections even where curvature is mild. A correct offset therefore requires detecting these degeneracies and *trimming* the invalid regions, not merely displacing points.

The engineering takeaways are concrete. The maximum safe uniform shell or fillet is bounded by the smallest concave radius of curvature anywhere on the wall, so a designer who requests a wall thicker than the tightest internal radius will hit a self-intersection failure rather than a clean result. And because the exact offset is unattainable in closed form, exchanging offset geometry between systems relies on the approximated NURBS plus the trim loops, which is why offset-heavy models are sensitive to tolerance settings and can differ subtly across kernels.
