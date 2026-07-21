Ruled and lofted surfaces both build a surface by *interpolating between input curves*, but they differ in how many curves they blend and how smoothly. They are the backbone of free-form surfacing where a shape is specified by its cross-sections rather than by a control grid.

## Ruled surfaces

A *ruled* surface linearly interpolates between two boundary curves \(\mathbf{C}_0(u)\) and \(\mathbf{C}_1(u)\):
\[ \mathbf{S}(u,v) = (1-v)\,\mathbf{C}_0(u) + v\,\mathbf{C}_1(u), \qquad v \in [0,1]. \]
For each fixed \(u\) the surface contains a straight-line *ruling* joining corresponding points on the two curves, so the surface is "woven" from straight segments. Ruled surfaces matter industrially because a subclass of them are *developable*: if the tangent plane is constant along each ruling, the Gaussian curvature is zero everywhere and the surface can be *unrolled flat without stretching*. That is the geometric condition behind sheet-metal, plate, and fabric development, and behind wire-EDM and hot-wire cutting where the tool is a straight line. Note that the two input curves must share a consistent parameterization; a mismatch produces skewed rulings and an unintended shape.

## Lofted (skinned) surfaces

A *loft* (or *skin*) generalizes this to a family of section curves \(\mathbf{C}_0(u), \mathbf{C}_1(u), \dots, \mathbf{C}_K(u)\) placed at parameters \(v_0 < v_1 < \dots < v_K\), and fits a surface that *passes through every section*. In the \(u\)-direction the surface simply inherits the sections' NURBS form; in the \(v\)-direction the modeler chooses a degree and solves an *interpolation system* for the intermediate control-point rows so that \(\mathbf{S}(u, v_k) = \mathbf{C}_k(u)\). Additional constraints - end tangency to an adjacent surface, or a prescribed normal - are added as equations in the same linear system.

The practical prerequisite is *compatibility*: all section curves must share one common degree and one common knot vector before they can be blended. Since sections are authored independently, the modeler first *degree-elevates* the lower-degree sections and *merges knots* (knot refinement) so every section has the identical basis in \(u\); only then are the control points aligned row by row for the \(v\)-interpolation. Choosing the \(v_k\) values (uniform, chord-length, or centripetal parameterization) controls fullness and guards against overshoot between widely spaced or dissimilar sections, exactly as parameterization choice does for curve interpolation.
