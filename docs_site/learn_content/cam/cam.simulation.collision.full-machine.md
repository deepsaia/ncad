Full machine simulation lifts verification from the tool-and-part neighborhood to the entire machine tool. Instead of only the cutter, holder, and stock, it models every physical body in the kinematic system — the bed, saddle, table, rotary trunnions, column, spindle housing, tailstock, turrets, tool changers, guards, and the fixtures and workpiece riding on them — and drives them from the actual axis commands the machine will execute. The purpose is to catch failures that a part-only simulation cannot see: an axis exceeding its travel limit, the head crashing into the enclosure or a clamp far from the cut, or a rotary move that swings the workpiece into the column.

## Kinematic model of the machine

A machine tool is a chain of rigid links connected by prismatic (linear) and revolute (rotary) joints. Each axis contributes a homogeneous transform \(T^{i-1}_{i}(q_i)\) that depends on its commanded value \(q_i\) — a translation for a linear axis, a rotation for a rotary axis. The pose of any body relative to the machine frame is the ordered product of the transforms from the base up its branch of the chain,

\[
T^{0}_{n}(\mathbf{q}) \;=\; \prod_{i=1}^{n} T^{i-1}_{i}(q_i),
\]

so a single vector of axis positions \(\mathbf{q}=(X,Y,Z,A,B,C,\dots)\) places every link in space simultaneously. This **forward-kinematics** evaluation, done at each interpolated step of the program, is what turns a stream of axis words into a fully posed machine that can be collision-tested and travel-checked. Because the tool tip pose depends on the whole chain, five-axis programs that hold a point in space while rotating (rotation-around-tool-center behavior) only stay correct if the simulator uses the *same* kinematic chain the controller does.

## Post-processed code, not idealized moves

The defining feature of full machine simulation is that it runs on the **post-processed output** — the actual axis commands in the machine's dialect — rather than the idealized cutter-location path from the toolpath planner. This is what makes it a check on the post-processor and the machine configuration, not just the toolpath. The chain from intent to motion is: toolpath >> neutral cutter-location data >> post-processor >> controller code (per ISO 6983 axis-word conventions, with axis identities per the standard machine-coordinate nomenclature) >> the machine's kinematics. A part-only simulation validates the first stage; full machine simulation validates the whole chain, including axis-limit violations, rotary singularities and unwinds, non-linear five-axis positioning error between blocks, and collisions with structures that exist only in the real machine.

## Where it matters

Full machine simulation is essential wherever the machine envelope is crowded or the motion is not a simple tool sweep: multi-axis mills with tilting rotary tables, mill-turn and multi-turret lathes where turrets and sub-spindles share the work zone, bar feeders and part catchers, robotic or pallet automation cells, and any job pushing the limits of travel or clearance. It is also the geometric backbone of a machine **digital twin**, where the same kinematic model that verifies a program offline can be driven by live axis feedback to visualize and monitor production. Its two hard requirements are an accurate 3-D model of the machine's bodies and an exact kinematic definition matching the real controller; when either is approximate, the simulation can give false confidence, so a defensible workflow validates the machine model against known geometry before trusting its collision verdicts.
