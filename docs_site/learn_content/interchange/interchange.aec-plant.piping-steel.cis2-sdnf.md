Structural steelwork passes through a chain of silos: structural analysis, design code checking, connection design, detailing, CNC fabrication, and erection management. Two neutral formats dominate the handoff between them. CIS/2 (the CIMsteel Integration Standards, Release 2) is the rich, STEP-based standard; SDNF (Steel Detailing Neutral Format) is the older, lightweight, record-based format. Both exist to move a fabrication-ready steel model, members, sections, materials, and (for CIS/2) connections and analysis results, between tools while preserving each piece's identity so its status can be tracked by piecemark and assembly mark.

## CIS/2: a STEP-based logical product model

CIS/2 is built on STEP technology (ISO 10303): its schema is written in the EXPRESS language (ISO 10303-11) and exchanged as a Part 21 physical file, giving it the same formal, machine-verifiable footing as other STEP application protocols. Its Logical Product Model spans three coordinated views of the same structure: an *analysis* model (nodes, elements, restraints, load cases, and results), a *design* model (design members and their code-check context), and a *manufacturing/detailing* model (physical parts, assemblies, holes, bolts, welds, and surface treatment). Because the schema is semantic, a bolted moment connection can be transferred as an object with its bolt group, grade, and weld sizes intact, rather than as loose geometry, which is what allows connection design and fabrication data to flow without re-modeling.

## SDNF: a pragmatic record format

SDNF takes the opposite approach: it is a simple ASCII file organized into numbered packets (for example packet 20 for linear members), where each member record lists its two work-point end coordinates, section designation, material grade, member type, and orientation. It carries little connection detail and no analysis results, but its simplicity is its strength. It is robust, easy to parse, and near-universal, so it survives as a lingua franca for exchanging member positions and section assignments, especially when integrating structural steel into a broader 3D plant or coordination model where full CIS/2 semantics are unnecessary.

## The shared geometric model

Both formats describe steel as a wireframe of member centerlines plus section orientation, so the receiving tool can regenerate the solid. A prismatic member is defined by two work-point nodes \(P_1, P_2\) and a roll angle. Its local longitudinal axis is the unit vector along the centerline,

\[ \hat{\mathbf{x}} = \frac{P_2 - P_1}{\lVert P_2 - P_1 \rVert}, \]

and the section's principal axes \((\hat{\mathbf{y}}, \hat{\mathbf{z}})\) are fixed by choosing a reference up-direction, projecting it perpendicular to \(\hat{\mathbf{x}}\), and applying the roll angle about \(\hat{\mathbf{x}}\). A cardinal point (setout point) then offsets the profile from the centerline so that, for example, a beam sits with its top flange on the reference line. Preserving \(P_1, P_2\), the roll angle, and the cardinal point is what keeps members correctly positioned and oriented across the exchange; losing the cardinal point silently shifts steel by half a section depth.

## Choosing between them

The practical trade-off is expressiveness versus ubiquity. CIS/2 can carry the complete engineering intent, analysis, design, and detailed connections, and is the right choice when connection design or analysis-to-fabrication traceability must survive the transfer; its cost is a heavier schema and stricter conformance. SDNF carries far less but is trivial to produce and consume, which is why it remains the default for coarse member-level exchange and for feeding steel geometry into non-steel disciplines. In many real projects both are used: SDNF for quick geometry hand-off and CIS/2 (or increasingly the structural extensions of open building-model standards) where semantic fidelity matters. The unifying idea behind both is stable part and assembly identity, so that a piece detailed in one system can be fabricated, tracked, and erected as the same recognizable object everywhere downstream.
