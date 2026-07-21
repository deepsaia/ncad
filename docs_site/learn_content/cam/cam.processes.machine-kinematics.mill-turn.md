Mill-turn (multi-tasking) machines merge turning and milling in one work envelope so a part can be roughed, turned, drilled off-center, and milled without moving to a second machine. The motivation is setup reduction: every re-fixturing introduces a locating error and adds handling time, so completing a part *in one clamping* both raises accuracy and shortens the process chain. Physically, these machines add a milling spindle with **live tooling** (driven rotating tools) to a lathe-style turning spindle, plus the extra axes needed to place those tools anywhere on the rotating stock.

## The C-axis and interpolated cylindrical work

The key enabler is turning the main spindle into a **controlled rotary axis**, the **C-axis**, so the workpiece can be indexed or continuously interpolated to an exact angular position rather than merely spun. Combined with a radial **Y-axis** offset from the turning centerline, this lets a live tool cut flats, hexagons, keyways, and off-axis holes. Two interpolation modes make wrapped features possible:

- **Polar interpolation** coordinates a linear axis with the C-axis to machine a contour on a face as if it were a flat X-Y plane.
- **Cylindrical interpolation** coordinates feed along Z with C-axis rotation to cut a groove or slot that wraps around the cylindrical surface; the controller converts a programmed unrolled path length into the required angular advance \(\theta = s/r\) at radius \(r\).

Many machines add a **sub-spindle** (a second turning spindle facing the first) so a part can be gripped, cut off, and transferred to have its back side finished without operator intervention. When both spindles turn a shared part, or when a bar is passed between them, their rotations must be **synchronized**: the controller locks the two spindle angles in phase, and the transfer is done at matched speed to avoid marking or slipping the part.

The payoff is done-in-one production of complex prismatic-on-round parts (shafts with milled features, valve bodies, medical and aerospace components). The costs are programming and simulation complexity, because independent turrets, spindles, and tool carriers can collide, and because the process plan must interleave turning and milling operations while respecting thermal growth and chip evacuation in a crowded envelope.
