Extruded, revolved, and swept surfaces are *procedural* (constructive) surfaces: instead of positioning a grid of control points, the designer supplies a *generator* (or profile) curve and a rule for moving it through space. The trajectory sweeps the profile into a surface. These constructions map one-to-one onto the most common modeling features and, importantly, all three have exact NURBS forms, so the procedural intent and the evaluable surface coexist.

## The three families

An *extrusion* (translational sweep) slides a profile \(\mathbf{C}(u)\) along a fixed direction \(\mathbf{d}\):
\[ \mathbf{S}(u,v) = \mathbf{C}(u) + v\,\mathbf{d}, \qquad v \in [0, h]. \]
Every iso-line in \(v\) is a straight ruling parallel to \(\mathbf{d}\), so an extrusion is a special developable (a generalized cylinder). A *revolution* rotates a profile about an axis \((\mathbf{o}, \mathbf{a})\):
\[ \mathbf{S}(u,\theta) = \mathbf{o} + R_{\mathbf{a}}(\theta)\big(\mathbf{C}(u) - \mathbf{o}\big), \]
where \(R_{\mathbf{a}}(\theta)\) is rotation by \(\theta\) about \(\mathbf{a}\). The rotational direction is represented exactly with the *rational quadratic circle* (weights \(\sqrt2/2\) at the span midpoints), so a full revolution is an exact closed NURBS surface; where the profile touches the axis the surface degenerates to a pole. A *general sweep* moves a section curve along an arbitrary *spine* (path) curve, orienting the section by a moving coordinate frame at each point of the spine.

The hard part of a general sweep is *frame control*. The section must be oriented consistently as it travels; a naive Frenet frame (built from the spine's tangent, normal, and binormal) flips or spins wildly wherever the spine has an inflection or low curvature, injecting unwanted twist into the surface. Professional sweeps use a *rotation-minimizing frame* (also called a parallel-transport frame) that carries the section without spurious rotation, optionally with an explicit twist law or a guide curve that pins the section's orientation. Additional inputs let the section scale or morph along the path.

The other recurring pitfall is *self-intersection*. When the spine curves more tightly than the section is wide - specifically when the local radius of curvature of the spine drops below the section's radial extent on the concave side - the swept surface folds back on itself and becomes invalid. This is the same offset-distance-versus-curvature limit that governs offset surfaces, and robust sweepers detect and trim (or reject) such regions rather than emit self-intersecting geometry.
