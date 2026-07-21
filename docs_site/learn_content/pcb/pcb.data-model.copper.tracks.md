A **track** (trace) is a length of copper on a specific layer that carries a net's signal or power from one pad or via to another. Geometrically it is a *centerline polyline* with an associated **width** and layer index; the physical copper is the sweep of that width along the centerline, with defined corner treatment (45-degree miters or arcs). **Routing** is the process of realizing a schematic's net list as a manifold of such tracks that respects clearance, width, layer, and length rules.

Track **width** is not free: it is set by the current the conductor must carry and, for high-speed nets, by target impedance. The empirical current-versus-temperature-rise relation standardized for board conductors takes the form

\[ I = k\,(\Delta T)^{0.44}\,A^{0.725}, \]

where \(I\) is current in amperes, \(\Delta T\) is the allowed temperature rise, \(A\) is the cross-sectional area (width times copper thickness), and \(k\) is a constant that differs for external versus internal layers (internal traces run hotter because the surrounding dielectric impedes heat loss). Solving for area shows why a power trace on an inner layer must be considerably wider than the same current on an outer layer, and why copper weight and width trade off against each other.

For controlled-impedance nets the width, the dielectric thickness to the reference plane, and the material permittivity jointly set the characteristic impedance. A single-ended surface trace over a plane (microstrip) follows an approximation of the form

\[ Z_0 \approx \frac{87}{\sqrt{\varepsilon_r + 1.41}}\,\ln\!\left(\frac{5.98\,h}{0.8\,w + t}\right), \]

with \(h\) the dielectric height, \(w\) the trace width, and \(t\) the copper thickness; buried traces between two planes (stripline) have their own form. Differential pairs add coupling and require length matching, which is why routed geometry often includes deliberate serpentine tuning and tightly controlled spacing.

Because routing is a large combinatorial optimization (thousands of nets, clearance and via costs, layer assignment), it is frequently produced by specialized routing engines and then **consumed as geometry** by a downstream board or mechanical model. In that ingestion role the data of interest is the finished centerline, width, and layer of each segment, plus its net membership, rather than the search that produced it. Design-rule checks then verify minimum width, minimum clearance to foreign copper, and any impedance-class width constraints against the actual geometry.

Modeling tracks as *net-tagged centerlines with width and layer* (rather than as opaque filled polygons) keeps them editable, checkable, and cheap to store, and it preserves the connectivity graph that the rest of the board model, from netlist verification to plane return-path analysis, depends on.
