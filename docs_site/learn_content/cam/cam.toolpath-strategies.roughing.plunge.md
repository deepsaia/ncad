Plunge roughing (also called plunge milling or Z-axis roughing) removes bulk stock by a dense sequence of **axial drilling-like plunges** with an end mill, stepping the tool over between plunges to cover the area, instead of cutting laterally with the side of the flutes. Each plunge drives the cutter straight down into the material along the spindle axis, retracts, shifts by a small step, and plunges again. It is the roughing strategy of choice when the tool must reach deep into a cavity with a long overhang, precisely the situation where side-milling forces would bend the tool.

The reason is the **direction of the cutting force**. In side milling the dominant force is radial, perpendicular to the tool axis, which deflects a long slender tool as a cantilever; deflection grows with the cube of overhang length. In plunging, the dominant force is **axial**, directed straight up the tool and into the spindle bearings, where the structure is stiff and the tool is loaded in compression rather than bending. A long-reach or small-diameter tool can therefore take a heavy cut deep in a pocket with minimal deflection and chatter, which is why plunge roughing dominates deep-cavity mold work and hard-to-reach features.

The stepover between plunges sets both the scallop of leftover stock and the peak load. Plunges are typically overlapped so the effective radial step is a fraction of the diameter; adjacent plunge craters leave cusps of uncut material between them that a later semi-finish pass removes. The material removal rate is

\[ \text{MRR} \approx \frac{V_{\text{plunge}}}{t_{\text{plunge}} + t_{\text{retract}} + t_{\text{index}}}, \]

so the productivity is limited by the non-cutting retract and index time between holes; large axial depths per plunge and rapid retracts are what make it competitive.

## Tool and practical constraints

Plunge milling demands cutters designed to cut on the **end**, with center-cutting geometry and adequate chip room, because chips are formed at the bottom and must escape up the flutes without packing (chip evacuation is the main failure mode). Not all end mills can plunge; a tool without center-cutting flutes will rub and burn. The strategy is comparatively rough, it leaves a stepped, scalloped floor and cannot finish, so it is strictly a bulk-removal precursor. Its niche is unambiguous: whenever tool overhang is large enough that lateral cutting would chatter or deflect out of tolerance, plunging converts the load into the one direction the machine and tool handle best.
