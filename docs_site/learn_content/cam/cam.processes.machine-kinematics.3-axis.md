A 3-axis milling machine positions a rotating tool with three mutually orthogonal **linear axes**, conventionally X, Y, and Z. The tool spins about a fixed axis (usually parallel to Z), so its *orientation never changes*: only the tool tip's position is commanded. This is the simplest and most common machining kinematics, and the constraint of a fixed tool axis is precisely what makes it predictable, rigid, and easy to program, while also bounding what geometry it can reach.

Motion is produced by **interpolation**: the controller drives the three servo axes in coordination so the programmed feature is traced at a commanded feed rate. Linear moves interpolate a straight line between endpoints; circular moves hold two axes on an arc. The path is sampled into small increments each servo cycle, and the axes are commanded so their vector sum follows the toolpath while the resultant speed equals the programmed feed \(v_f\).

## The scallop-height limit on finish

With a ball-end tool finishing a surface by adjacent parallel passes, material left between passes forms a ridge, the **scallop** (or cusp). For a tool of radius \(R\) and stepover \(a_e\), the residual height is

\[ h = R - \sqrt{R^{2} - \left(\tfrac{a_e}{2}\right)^{2}} \;\approx\; \frac{a_e^{2}}{8R}. \]

Because \(h\) grows with the square of the stepover, halving \(a_e\) quarters the scallop, which is the direct trade-off between surface finish and machining time on 3-axis finish passes.

<svg viewBox="0 0 240 90" width="240" height="90" stroke="currentColor" fill="none" stroke-width="1.5" aria-label="Two adjacent ball-nose passes leaving a scallop cusp"><path d="M20 20 A40 40 0 0 0 100 20"/><path d="M80 20 A40 40 0 0 0 160 20"/><line x1="20" y1="70" x2="160" y2="70"/><line x1="60" y1="20" x2="120" y2="20" stroke-dasharray="3 3"/><line x1="90" y1="20" x2="90" y2="38"/><text x="96" y="32" font-size="10" stroke="none" fill="currentColor">h</text><text x="60" y="14" font-size="9" stroke="none" fill="currentColor">stepover a_e</text></svg>

A large share of practical work is **2.5D**: pockets, bosses, and holes machined at constant Z, where each level is a 2D contour and depth is stepped down. True 3D surfacing drives all three axes simultaneously along a curved surface. The defining limitation of the fixed tool axis is that any **undercut**, a feature whose surface faces partly back toward the tool, is unreachable, and tall thin tools needed to reach deep pockets deflect and chatter. These constraints motivate the added rotary axes of 4- and 5-axis machines.
