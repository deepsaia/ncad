STEP-NC is a data model for CNC manufacturing that replaces the low-level move-by-move description of G-code with a high-level, *feature-based* description of the machining task. It is standardized as ISO 14649 (the Application Reference Model) and, in an integrated form, as ISO 10303-238 (Application Protocol 238, which expresses the same content in the EXPRESS schema and STEP file infrastructure of the broader product-model standard). The motivating idea is to send the controller *what* to make and *why*, not merely a stream of coordinated axis moves. Instead of thousands of `G01`/`G02` blocks, a STEP-NC program carries the workpiece geometry, the manufacturing features (pockets, holes, slots, threads, planes), the machining *workingsteps* that produce them, tolerances, tools, strategies, and the setup, all as structured, typed objects.

## The Workplan / Workingstep / Operation model

The execution backbone is a *Workplan*: an ordered list of *executables*. The principal executable is the *Workingstep*, which binds together three things: the manufacturing *feature* to be machined, the *operation* (for example rough milling, finish milling, drilling) with its technology and strategy parameters, and the *tool* required. Features are defined on a workpiece and carry their own geometry and tolerances, so the machine (or an intelligent controller) has enough information to derive toolpaths rather than merely replay them. Schematically:

<svg viewBox="0 0 460 150" stroke="currentColor" fill="none" stroke-width="1.5" font-size="11">
 <rect x="10" y="55" width="90" height="40" rx="4"/>
 <text x="55" y="79" fill="currentColor" stroke="none" text-anchor="middle">Workplan</text>
 <line x1="100" y1="75" x2="140" y2="75"/>
 <rect x="140" y="55" width="100" height="40" rx="4"/>
 <text x="190" y="79" fill="currentColor" stroke="none" text-anchor="middle">Workingstep</text>
 <line x1="240" y1="75" x2="290" y2="20"/>
 <line x1="240" y1="75" x2="290" y2="75"/>
 <line x1="240" y1="75" x2="290" y2="130"/>
 <rect x="290" y="5" width="160" height="30" rx="4"/>
 <text x="370" y="24" fill="currentColor" stroke="none" text-anchor="middle">Feature (+ tolerances)</text>
 <rect x="290" y="60" width="160" height="30" rx="4"/>
 <text x="370" y="79" fill="currentColor" stroke="none" text-anchor="middle">Operation (+ strategy)</text>
 <rect x="290" y="115" width="160" height="30" rx="4"/>
 <text x="370" y="134" fill="currentColor" stroke="none" text-anchor="middle">Tool (+ technology)</text>
</svg>

## Why replace G-code

A G-code program is post-processed for one machine, one controller dialect, and one tool set; it discards the design and process intent, so it cannot be re-targeted, re-optimized, or verified against the part without returning to the CAM system. STEP-NC keeps that intent in the file. Because features and tolerances travel with the program, a controller can adapt: substitute an available tool, re-sequence independent workingsteps, regenerate a toolpath for different kinematics, or apply on-machine measurement and closed-loop correction against the stated tolerance. The model is also *bidirectional* in principle, allowing as-machined results and shop-floor changes to flow back toward the design, which supports a genuine round trip rather than the one-way street of a post-processed NC program.

## Interpolation, strategies, and technology

STEP-NC still supports explicit toolpaths when they are needed (including higher-order path elements beyond straight lines and circular arcs, such as polynomial and NURBS-defined curves), but it prefers to describe *strategy*: for a pocket, a spiral or contour or zig-zag approach with stepover and stepdown; for a hole, a drilling cycle with peck and dwell. Technology objects carry feeds, speeds, cutting depth, and coolant as named parameters attached to the operation, and machine functions capture spindle, coolant, and clamping state. This separation of feature, strategy, and technology is what lets the same task description be realized differently on different equipment while still guaranteeing the specified geometry and tolerances.

## Adoption and where it matters

The practical significance of STEP-NC is greatest wherever the loss of intent in G-code is costly: distributed and multi-vendor manufacturing, adaptive and autonomous machining, on-machine inspection, digital-thread and traceability initiatives, and long-life or high-value parts that may be re-manufactured years later. Adoption has been gradual because it requires either intelligent controllers that interpret the model directly or shop-floor tools that expand it into machine-specific motion, and because the installed base of G-code post-processors is enormous. Even so, ISO 14649 and AP 238 remain the reference for how a manufacturing task should be described when the goal is portability, verifiability, and preservation of engineering intent across the CAD-CAM-CNC chain.
