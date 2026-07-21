Adding **rotary axes** to the three linear ones lets a machine change the *orientation* of the tool relative to the part, not just its position. A single rotary axis (4-axis) is common for indexing or continuous rotation of a workpiece; two rotary axes (5-axis) give full control of the tool vector, so a curved surface can be machined with the tool held at an ideal lead and tilt everywhere. This reaches undercuts, keeps a ball tool off its dead-center point (where cutting speed is zero), and lets a single setup access faces that would otherwise need re-fixturing.

## Where the rotary axes live

The two rotaries can be placed on the tool, on the part, or split between them, and this defines the machine's kinematic class:

- **Head-head** (both rotaries carry the spindle): the tool tilts; the part stays fixed, favoring very large workpieces.
- **Table-table** (both rotaries carry the part, a trunnion/cradle): the part tilts and rotates; the tool stays vertical, giving rigidity but limiting part size and mass.
- **Head-table** (one rotary on the tool, one on the part): a hybrid balancing reach and rigidity.

## Forward kinematics and RTCP

The machine's job is to realize a commanded tool tip position and tool axis direction through the joint values. Each rotary contributes a rotation matrix, and the tool axis in the part frame follows from composing them. For a table-table machine with a tilt \(A\) about X carried on a rotation \(C\) about Z, the tool direction expressed in part coordinates is

\[ \mathbf{o}_{\text{part}} = \big(R_x(A)\,R_z(C)\big)^{-1}\,\hat{\mathbf z} = R_z(-C)\,R_x(-A)\,\hat{\mathbf z}. \]

Because rotating the part or head sweeps the tool tip away from where it was, controllers provide **RTCP** (rotational tool-center-point control, also called TCPC): the controller compensates the three linear axes in real time so the programmed point remains the *tool tip in the part frame* regardless of rotary position. This decouples programming (in part coordinates) from the specific machine geometry, and it is why a **postprocessor** must encode the exact kinematic chain, axis limits, and pivot offsets of the target machine.

Five-axis motion introduces **singularities**: near an orientation where the two rotary axes align, a small change in tool direction demands a near-infinite rotary velocity, causing dwell marks or overspeed faults. Toolpaths are smoothed or reoriented to avoid these poles, and axis travel limits mean the same tool vector can often be reached by multiple joint solutions, of which the planner must pick the collision-free, in-range one.
