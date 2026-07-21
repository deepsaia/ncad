**Sectioning** cuts a solid or surface with a family of planes and extracts the resulting intersection curves. Slicing with parallel constant-\(Z\) planes yields the level contours that drive *waterline* (z-level) finishing and 2.5D contour roughing; slicing with an arbitrary plane gives cross-sections for inspection or profile extraction. The name "waterline" is the intuition: flood the part up to height \(z\) and the shoreline is the contour to machine at that level.

## The governing idea

For a parametric surface \(S(u,v)\) intersected with the plane \(z = c\), the contour is the solution set of

\[ S_z(u,v) = c, \]

a curve in parameter space that lifts to a 3D space curve. In general this is a surface-plane (a special surface-surface) intersection: an implicit condition solved by a **marching** scheme that finds a start point, then steps along the curve, at each step taking a predictor along the estimated tangent and a Newton corrector back onto both surfaces to within tolerance. The output is an ordered polyline or a fitted spline that honors a chordal deviation bound.

For a boundary-representation solid the operation is topological as well as numerical. Each face is intersected with the plane to produce candidate edge fragments; those fragments are then trimmed to the face's parametric domain, oriented, and stitched end-to-end into closed wires. Correct stitching must respect the model topology so that shared edges join exactly, multiple disjoint loops at one level are separated, and nesting (which loops are outer boundaries and which are holes/islands) is recovered so the contour can be used as a machining region.

## Where it matters

Constant-\(Z\) sections are the standard finishing strategy for steep walls, where the near-vertical geometry gives well-spaced contours and controlled scallop, complementing the drop-cutter/parallel approach that excels on shallow faces. The same slices, taken coarsely, define roughing levels: the material between successive planes is removed by pocketing inside each contour. Sectioning also supplies silhouette and profile curves, 2.5D pocket boundaries, and the cross-sections used for measurement and documentation.

## Failure modes to respect

The fragile cases are geometric tangencies and degeneracies. When a plane grazes a surface tangentially the intersection degenerates to a point or a region rather than a clean curve, and Newton correction stalls; when the plane passes exactly through a vertex or along an edge the topology is ambiguous. Robust implementations perturb or special-case these, keep a single global tolerance so that marching, trimming, and stitching all agree, and classify each contour's material side so downstream offsetting inflates in the correct direction. Getting the loop orientation and nesting right is what separates a usable contour set from a tangle of unordered segments.
