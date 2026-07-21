Patterning (instancing) replicates a *seed* feature or body into many copies that remain governed by a small set of parameters, so that changing the count, spacing, or driver updates every instance at once. Linear and circular patterns cover regular arrays and bolt circles, but real parts often need instances that follow a shape, land on chosen points, come from a data table, or fill a region. These *advanced drivers* keep the replication associative to the geometry that defines it, which is both their power and their fragility: the pattern is only as stable as the curve, sketch, region, or table it references.

## Curve-driven patterns

A curve-driven pattern distributes instances along a guide curve, which requires reasoning about arc length rather than parameter value, because a parametric curve \(\mathbf{C}(t)\) is generally not traversed at constant speed. The arc length from the start to parameter \(t\) is

\[ s(t) = \int_{t_0}^{t} \left\| \mathbf{C}'(u) \right\| \, du. \]

Equal *spacing* places instance \(i\) at the parameter \(t_i\) solving \(s(t_i) = i\,\Delta s\) (typically by inverting the arc-length function numerically), whereas equal *parameter* spacing uses \(t_i = t_0 + i\,\Delta t\) and bunches instances where the curve moves slowly. Orientation is a separate choice: instances may hold a fixed world orientation, or align to the curve's moving frame so that each copy tangent-follows the path (rotating with the unit tangent \(\mathbf{T}(t) = \mathbf{C}'(t)/\lVert \mathbf{C}'(t)\rVert\)). This is the natural driver for features that trace a contour, a rib, or a decorative edge.

## Sketch-, point-, and table-driven patterns

When instance locations are irregular but explicit, three related drivers apply. A *sketch-driven* (point-driven) pattern places one instance at each point of a reference sketch, mapping a chosen reference point on the seed onto every sketch point; this is ideal when the layout is itself designed geometrically and should stay associative to that layout. A *table-driven* pattern reads instance coordinates from an explicit list of \((x, y)\) (optionally \(z\)) offsets measured in a named coordinate system, which suits standardized hole charts and data exchanged as tabular values. The two differ mainly in provenance: sketch-driven intent lives in editable geometry and constraints, table-driven intent lives in numeric records, and each is easier to author and audit for its respective use.

## Fill patterns

A fill pattern populates a bounded region (a face or a closed sketch region, minus specified islands and a boundary margin) with a repeating layout. Common layouts are the aligned grid, the staggered or hexagonal lattice, concentric or spiral arrangements, and user-defined polygonal tilings, controlled by instance spacing, boundary offset, and stagger angle. The hexagonal (triangular) lattice matters because it is the densest arrangement of equal circles in the plane, with packing fraction

\[ \eta = \frac{\pi}{2\sqrt{3}} \approx 0.9069, \]

versus \(\pi/4 \approx 0.7854\) for a square grid, so hex fills give more instances (perforations, lightening holes, cooling features) per unit area for a given clearance. Fill patterns must also decide how to treat instances that would cross the boundary or an island, either clipping them or dropping partial copies.

<svg viewBox="0 0 320 90" stroke="currentColor" fill="none" stroke-width="1.5" aria-label="Curve-driven versus hex-fill layouts">
  <path d="M8 70 Q 60 10 110 55 T 150 40" />
  <circle cx="8" cy="70" r="3"/><circle cx="55" cy="31" r="3"/><circle cx="96" cy="49" r="3"/><circle cx="131" cy="46" r="3"/>
  <rect x="200" y="12" width="104" height="66" rx="4"/>
  <g>
    <circle cx="218" cy="28" r="5"/><circle cx="240" cy="28" r="5"/><circle cx="262" cy="28" r="5"/><circle cx="284" cy="28" r="5"/>
    <circle cx="229" cy="47" r="5"/><circle cx="251" cy="47" r="5"/><circle cx="273" cy="47" r="5"/>
    <circle cx="218" cy="66" r="5"/><circle cx="240" cy="66" r="5"/><circle cx="262" cy="66" r="5"/><circle cx="284" cy="66" r="5"/>
  </g>
</svg>

## Shared concerns

All pattern drivers share a set of engineering considerations. The seed must produce valid geometry at every instance location: a boss patterned onto a face edge, or a cut that lands where there is no material, yields a failed or invalid solid, so patterns interact strongly with feature ordering and with the region actually available on the model. Instances should be individually suppressible so that a nearly regular layout with a few omissions need not abandon the pattern. And because each instance introduces new faces and edges, patterns amplify the persistent-naming problem for anything that later references patterned topology (a fillet on "all pattern holes," say). Treating patterns as associative features rather than one-time copies is what preserves the parametric intent through later edits.
