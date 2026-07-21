## From a layered 2D layout to 3D thin solids

A printed board is authored as a stack of 2D layers registered to a common origin in the board plane. The intelligent/manufacturing data describes only planar geometry plus a layer stackup that assigns each layer a z-position and a thickness: a board profile, interior cutouts and slots, copper features per conductor layer, a drill table, and soldermask/silkscreen artwork. "Lowering" is the deterministic step that turns this planar description into watertight 3D solids a mechanical model can consume: each planar region is realized as a linear extrusion (a right prism) along the board normal.

The core operator is the prism. Given a planar face \(F\) lying in the plane \(z=z_0\) and a thickness \(t\), the extruded solid is
\[ S = \{\,(x,y,z) : (x,y)\in F,\; z_0 \le z \le z_0 + t\,\}. \]
The board body is the extrusion of the board-profile face. That face is bounded by the outer profile wire (oriented counterclockwise) while every interior cutout, milled pocket, or slot contributes an inner wire (oriented clockwise), so the face carries holes with correct orientation. Plated and non-plated holes are either modeled as inner wires that run through the full stackup or subtracted as cylinders by a boolean difference. Correct winding is not cosmetic: it fixes the direction of the outward face normal and is what makes the resulting boundary representation a valid, closed solid rather than a non-manifold shell.

<svg viewBox="0 0 420 140" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1">
  <rect x="30" y="30" width="220" height="6"/>
  <rect x="30" y="36" width="220" height="50"/>
  <rect x="30" y="86" width="220" height="6"/>
  <line x1="120" y1="30" x2="120" y2="92"/>
  <line x1="150" y1="30" x2="150" y2="92"/>
  <text x="265" y="36" font-size="10" stroke="none" fill="currentColor">copper (~35 um)</text>
  <text x="265" y="64" font-size="10" stroke="none" fill="currentColor">dielectric core</text>
  <text x="265" y="94" font-size="10" stroke="none" fill="currentColor">copper (~35 um)</text>
  <text x="96" y="112" font-size="10" stroke="none" fill="currentColor">plated hole / cutout</text>
</svg>

Copper is the same operator applied to each conductor layer, but with a stackup-driven thickness. Foil is specified by area weight, and thickness follows from \( t = m/(\rho A) \): for copper (\(\rho \approx 8.96\ \mathrm{g/cm^3}\)) one ounce per square foot works out to roughly \(35\ \mu\mathrm{m}\). Every layer -- dielectric core, prepreg, copper, soldermask, silkscreen -- has its own z-offset \(z_i\) and thickness \(t_i\), so the assembled body is a sum of thin prisms stacked along the normal and the overall board thickness is \(\sum_i t_i\). This is why the lowering step needs the stackup, not just the artwork: the artwork gives the in-plane shape, the stackup gives the third dimension.

## Level of detail and robustness

Extruding every trace, pour, thermal relief, and via yields solids with millions of faces that no mechanical assembly needs and that stall downstream boolean and distance queries. A practical pipeline therefore selects fidelity: the dielectric board body and its cutouts are almost always kept, copper is often reduced to a single representative layer or to keepout envelopes, and curved features (arcs, filleted corners) are faceted to a chord tolerance that trades face count against geometric error. Robustness also demands cleaning the source contours first -- removing self-intersections, closing small gaps, and merging coincident vertices -- because an invalid input face makes the extrusion fail or produce a non-manifold result.

Where it matters: the board body and its cutouts are the shared datum between the electrical and mechanical domains. Mounting holes must line up with enclosure bosses, connector and switch cutouts with enclosure openings, and the board thickness governs the fit into card guides or edge slots. Making the lowering deterministic -- the same input layout produces an identical solid -- is what lets the two disciplines iterate against a stable, comparable 3D model instead of arguing about geometry that shifts on every export.
