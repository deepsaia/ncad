**Drop-cutter** is a point-sampling method for generating gouge-free 3-axis finishing paths over a triangulated surface or a height field. Conceptually you place the tool axis vertical at a plan-view point \((x, y)\) and lower the cutter along \(-Z\) until it first touches the model; the height at that instant is the cutter-location (CL) height. Sweeping the sample point along parallel lines produces raster/parallel finishing; sampling on a grid produces a full z-map of the machined surface.

## The governing computation

Because the tool must rest on the *highest* thing beneath it, the CL height is a maximum over all surface facets:

\[ z_{CL}(x,y) \;=\; \max_{t \,\in\, \text{triangles}} \; \mathrm{drop}(x, y, t). \]

Taking the maximum is what makes the result gouge-free by construction: if the tool sat any lower it would penetrate some triangle. For each triangle the drop test decomposes into three primitive contacts, and the facet's contribution is the maximum of the three:

- **Facet contact:** lower the tool until the signed distance from the cutter's defining point to the triangle's plane equals the tool geometry constraint.
- **Edge contact:** the tool touches a triangle edge (a line segment) tangentially.
- **Vertex contact:** the tool touches a triangle vertex.

For a ball-nose of radius \(r\), each case is closed form: contact with a plane occurs when the sphere center is at distance \(r\) from the plane, contact with an edge when the center-to-line distance is \(r\), and contact with a vertex when the center-to-point distance is \(r\). Flat and toroidal (bull-nose) end mills have analogous closed-form tests derived from their profile of revolution, so no iterative surface intersection is needed.

## Cusp height and stepover

Between two adjacent parallel passes at radial stepover \(s\), a ball tool of radius \(r\) leaves a residual ridge, the *scallop* or *cusp*. On a locally flat surface its height is well approximated by

\[ h \;\approx\; \frac{s^2}{8r}, \]

so finish quality is set by choosing \(s\) for a target \(h\). Because the method samples on a grid, the sampling density must be fine enough that the polyline through CL points does not itself introduce error, and near-vertical walls are effectively invisible to a top-down drop (they map to a single column), which is why drop-cutter for shallow regions is paired with constant-Z waterline paths for steep ones.

## Why it is used

Drop-cutter is popular precisely because it is robust and trivially parallel: every sample point is independent, so the whole grid maps cleanly onto many cores or a GPU, and there is no fragile surface-surface intersection to fail. It is also the natural engine for z-map based material-removal simulation and verification. Its limitations are the flip side of its strengths: grid sampling controls but does not eliminate discretization error, and it is inherently 3-axis (fixed vertical tool axis), so multi-axis or undercut work needs a different formulation.
