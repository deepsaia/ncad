Two-dimensional polygon offsetting is the workhorse of 2.5D machining. Given a closed region boundary, inflating or deflating that boundary by a signed distance \(d\) produces the geometry that drives profiling, pocket clearing, and tool-radius compensation. To cut a profile with a cutter of radius \(r\), the tool-center path is simply the part boundary offset inward by \(r\); to clear a pocket, a family of offsets spaced by the radial stepover fills the interior with concentric loops. The whole problem is therefore reducible to a single robust primitive: compute the offset of a set of polygons, then combine the results with Boolean operations.

## The governing idea

Offsetting is a Minkowski operation. Growing a region \(P\) outward by \(r\) is the Minkowski sum with a disk \(D_r\), and shrinking it is the corresponding erosion:

\[ P \oplus D_r = \{\, p + q : p \in P,\; q \in D_r \,\}, \qquad P \ominus D_r = \{\, x : x + D_r \subseteq P \,\}. \]

Concretely, each edge is translated along its outward normal by \(d\). Convex corners open a gap that is bridged by a circular arc of radius \(|d|\) (a *round* join) or by a straight *miter* or *square* join; reflex corners cause the translated edges to cross, creating self-intersections that must be cleaned up. The offset of a polyline (an open path) is handled by capping the endpoints with a round, square, or butt cap, exactly as in stroke rendering.

## Robustness: turn offsetting into clipping

The defining difficulty is topological. When a region is deflated, features pinch off, split into pieces, or vanish entirely once the offset exceeds the local half-width of the shape (the medial-axis radius). A naive per-edge offset leaves behind spurious self-intersecting loops. The robust cure is to offset every edge independently and then resolve the mess with a polygon-clipping engine: take the union of the inflated edge quads for an outward offset, or apply a non-zero winding rule to discard the invalid inner loops. This casts offsetting as a Boolean/clipping problem solved by a scanline sweep such as Vatti's algorithm, which handles arbitrary self-intersection, holes, and multiple contours in one pass.

Numerical robustness is the other half of the story. Floating-point coordinates make near-collinear and near-coincident vertices fragile, producing cracks and spurious slivers. Production offsetting libraries scale coordinates to integers and run the sweep in exact integer arithmetic, so intersection tests are decided exactly and the output topology is guaranteed consistent. Arcs from round joins are approximated by short chords to a controllable tolerance so the result stays a polygon set.

## Where it matters

Beyond simple profile compensation, offsetting underpins pocket roughing with a specified stock-to-leave (offset the wall inward by \(r + \text{stock}\)), rest-material computation (Boolean difference of the previous stock state and the current tool's reachable region), and island handling (offset outer boundary inward, island boundaries outward, then intersect). Because the entire family of operations is expressed as offset-then-Boolean on integer polygons, it is deterministic and reproducible, which is exactly what a rebuildable feature history requires.
