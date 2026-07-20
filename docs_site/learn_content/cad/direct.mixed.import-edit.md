**Import-and-edit** is the workflow that makes direct modeling essential: bring in a solid that has
**no feature history** (a STEP file from a supplier, a legacy part) and modify it in place with
direct edits, since there is no parametric tree to edit.

## Why history-free editing is needed

An imported B-rep is a "dumb solid": faces, edges, and vertices with exact geometry but no record of
*how* it was built. You cannot change an extrude's depth, there is no extrude. Direct operations,
move face, offset, defeature, relational alignment, are the only way to change such geometry: they
reshape the baked B-rep directly.

A typical session: import the STEP, defeature a vendor-specific boss, offset a mating face to adjust
a clearance, and make a face coaxial with your assembly's bore. Each edit references faces by a
persistent name derived from the imported topology (there is no construction lineage, so names seed
from the geometry itself), and each is guarded against the fragile cases so a bad edit is refused
rather than corrupting the solid.

Mixed modeling, a parametric tree for your own features plus direct edits for imported or baked
geometry, is how real CAD spans owned and third-party parts in one model.
