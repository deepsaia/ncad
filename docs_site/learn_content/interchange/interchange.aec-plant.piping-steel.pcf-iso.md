Process-plant piping is engineered and handed off through three distinct information layers, and the interchange formats in this area exist to move each layer between disciplines without loss. The schematic layer is the Piping and Instrumentation Diagram (P&ID): a topological, dimensionless graph of equipment, lines, valves, and instruments carrying tag numbers, service, and design conditions. The spatial layer is the 3D routed model: real centerlines, elevations, and clash-checked geometry. The fabrication layer is the isometric ("ISO"): a per-spool drawing with weld positions, spool breaks, bolt lists, and a bill of materials. A robust exchange must keep these layers reconciled through consistent line and component tagging, because they are authored in different tools at different project stages.

## P&ID exchange and ISO 15926

Exchanging a P&ID means exchanging connectivity and attributes, not shapes. The model is a directed graph in which nodes are equipment and inline components and edges are pipe segments, each element bound to a tag and a set of engineering properties. The lifecycle-integration standard ISO 15926 provides the underlying framework for representing and merging this data across the plant life cycle, using a reference data library and generic templates so that one tool's "gate valve" maps unambiguously to another's. Modern process-industry exchange (for example the DEXPI initiative) builds P&ID interchange on an XML schema aligned with ISO 15926 reference data, so that topology, tagging, and nozzle connectivity survive the transfer even when graphical presentation does not.

## The Piping Component File (PCF)

At the fabrication end, the Piping Component File is the de-facto neutral text format for a single isometric spool. It is a line-oriented ASCII file: a header block declares units, pipeline reference, and bore, then each component (`PIPE`, `ELBOW`, `TEE`, `FLANGE`, `VALVE`, `WELD`, and so on) is a keyword block listing end-point coordinates, bore, end type (butt-weld, socket, flanged), and item-code attributes that resolve to a material catalogue. Because a PCF encodes both geometry (end points and bore) and fabrication semantics (end types, welds, spool identity), it can drive automatic isometric drawing production and material take-off from a routed 3D model, decoupling the design tool from the drafting and MTO tools.

## Geometry that the formats must preserve

The fabrication layer turns on quantities computed from the routed centerline. For a bend of centerline radius \(R\) turning through angle \(\theta\) (radians), the developed (cut) length of pipe consumed by the arc is

\[ L_{\text{arc}} = R\,\theta, \]

while the tangent intersection point sits a setback

\[ t = R\,\tan\!\left(\frac{\theta}{2}\right) \]

back from the fitting's end along each leg. A spool's total cut length is the sum of straight runs plus arc lengths minus the material taken up by fittings and welds. Getting end-point coordinates, bores, and bend radii through the exchange intact is exactly what lets a downstream system recompute these values and produce a correct material list; a format that dropped bore or end-type would break the take-off even if the drawing still looked right.

## Why the layered approach matters

Separating schematic topology (P&ID), spatial geometry (3D), and fabrication detail (ISO/PCF) mirrors how a plant is actually engineered, and it lets each specialty own its authoritative data while still contributing to one coherent asset model. The recurring failure mode in plant projects is loss of tag continuity between these layers, so the governing design principle of all these formats is stable, cross-referenced identity: the same line number and component tag must appear in the diagram, the 3D model, the isometric, and ultimately the maintenance record, so that as-built and life-cycle data stay traceable.
