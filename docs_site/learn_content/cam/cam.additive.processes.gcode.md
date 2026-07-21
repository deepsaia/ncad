The final output of an additive process planner is a stream of machine instructions that command every motion and process event needed to build the sliced layers. For extrusion-based and many motion-driven machines this stream is a dialect of the numerical-control language standardized as RS-274, universally called G-code: a sequence of blocks, each a set of *words* (a letter address plus a value) such as `G1 X20 Y10 Z0.2 E1.5 F1800`. The canonical interpreter model defines the semantics: an ordered set of words per block, a controlled sequence of execution, and above all *modality*, where commands like motion mode, units, coordinate system, and feedrate persist until changed, so a block need only state what differs from the machine's current state.

## Motion, coordinates, and modality

The core of any toolpath is coordinated linear motion. `G0` performs a rapid (non-deposition) traverse and `G1` a controlled feed move along which material is added; the interpreter drives all named axes so they start and finish together, tracing a straight line in the configured coordinate system at the modal feedrate \(F\). Positions may be *absolute* (`G90`) or *incremental* (`G91`), expressed in a work coordinate system with programmable offsets, and arcs are available (`G2`/`G3`) where the machine supports them. This is the same kinematic core used in subtractive NC; additive planning simply restricts itself to the subset it needs and adds one crucial extra degree of freedom.

## The extrusion axis and volumetric balance

Extrusion additive machines model the filament (or paste) feed as an additional linear axis, conventionally `E`. The commanded \(E\) advance is not free: it is computed from mass conservation so that the volume of feedstock pushed in equals the volume of the deposited road. For a road of width \(w\) and height \(h\) laid along a path of length \(L\), fed from filament of diameter \(d_f\),

\[ \Delta E = \frac{w\,h\,L}{\tfrac{\pi}{4} d_f^{2}}, \]

so the planner emits synchronized \(X,Y,Z,E\) targets that keep the extrusion proportional to travel. *Retraction* (a negative \(\Delta E\) during rapids) relieves nozzle pressure to prevent stringing. Some controllers work in *volumetric* mode where \(E\) is expressed directly as \(w\,h\,L\) (a volume) and the firmware handles the filament geometry, which decouples the tuning of flow from the filament diameter.

## Process and auxiliary commands

Beyond motion, additive G-code carries the auxiliary (`M`) commands that manage the physics of consolidation: hot-end and bed temperature setpoints and their blocking wait-for-temperature variants, part-cooling fan control, and homing or bed-probing routines. A generated program is therefore a preamble that establishes state (units, absolute mode, heat-up, homing), a body of per-layer perimeter, infill, and support moves with interleaved \(Z\) increments, and an epilogue that retracts, turns off heaters and motors, and parks the head. Because the base language standardizes only a common core, individual firmwares extend it with vendor-specific codes; robust planners therefore target a documented flavor and rely on the modal, block-structured semantics that all dialects inherit from the RS-274/NGC model.
