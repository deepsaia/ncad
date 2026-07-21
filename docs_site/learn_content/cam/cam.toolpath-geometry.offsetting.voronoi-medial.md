The **medial axis** of a planar region is its skeleton: the locus of centers of all maximal inscribed disks, equivalently the set of interior points that have at least two distinct nearest points on the boundary. Attaching to each skeleton point the radius of its inscribed disk gives the **medial axis transform (MAT)**, which encodes both the shape's centerline and its local thickness. Because the MAT tells you the half-width of the material everywhere, it is a natural backbone for machining decisions that hinge on how much room the tool has.

## Relationship to the Voronoi diagram

For a polygonal region, the medial axis is a subset of the **Voronoi diagram** of the boundary elements (its vertices and edges). The Voronoi diagram partitions the plane into cells, one per site \(s_i\), where cell membership is decided by nearest site:

\[ V(s_i) = \{\, x : d(x, s_i) \le d(x, s_j)\ \text{for all } j \,\}. \]

Between two point sites the bisector is a straight line; between a point and a line segment it is a parabolic arc; between two segments it is again piecewise linear. The medial axis is obtained from this diagram by keeping only the bisectors that separate distinct boundary features and lie inside the region. For point sites, the diagram can be built in \(O(n \log n)\) by Fortune's sweepline; segment-site diagrams extend the same machinery with parabolic and linear bisector arcs.

## Why it matters for toolpaths

The radius function \(R(x)\) along the skeleton is the distance to the nearest wall, so it directly bounds the largest tool that can reach a given point: any cutter with radius greater than \(R(x)\) cannot pass through that neck. This immediately yields **maximum-inscribable-tool** analysis, **thin-wall and sliver detection**, and a principled way to decompose a complex pocket into machinable sub-regions. Spiral and offset pocketing strategies use the medial axis as the seed structure: offset loops are connected across the skeleton, and the branch points tell the linker where interior loops merge or split.

The skeleton is also the geometric basis for keeping cutter engagement bounded. Adaptive and trochoidal clearing strategies aim to hold the radial engagement angle nearly constant to protect the tool; knowing the local half-width from the MAT lets the planner predict where a naive contour-parallel path would slam the tool into a full-width slot (in a corner or narrow channel) and insert a smoother motion instead.

Computing the medial axis robustly is delicate because it is sensitive to small boundary perturbations, which can spawn spurious branches near noisy or nearly cocircular features. Practical implementations prune the skeleton with a significance measure and compute the underlying Voronoi structure in exact or filtered arithmetic to keep the topology stable.
