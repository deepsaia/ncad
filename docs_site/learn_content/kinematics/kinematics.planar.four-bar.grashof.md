A planar four-bar linkage is the simplest closed-loop mechanism that produces controlled, repeatable motion. It consists of four rigid links joined end to end by four revolute (pin) joints, with one link designated the fixed **frame** (or ground). The link adjacent to the frame that is intended to be driven is the **input** (often a crank), the opposite grounded link is the **output** (often a rocker), and the floating link joining them is the **coupler**. Because it is a single closed loop of pin joints in the plane, its mobility is one: a single input angle fully determines the configuration of every other link.

Mobility follows from the Kutzbach-Gruebler count for planar mechanisms,

\[ M = 3(n-1) - 2j_1 - j_2, \]

where \(n\) is the number of links (including ground), \(j_1\) is the number of one-degree-of-freedom joints (revolute or prismatic), and \(j_2\) is the number of two-degree-of-freedom joints. For the four-bar, \(n=4\), \(j_1=4\), \(j_2=0\), giving \(M = 3(3) - 8 = 1\). One actuator therefore drives the whole loop, which is why the four-bar is the workhorse of planar mechanism design.

## Grashof criterion

Whether a link can rotate fully (a crank) or only oscillate through a limited arc (a rocker) is decided by link-length proportions, not by which link is grounded. Label the shortest link \(s\), the longest \(l\), and the remaining two \(p\) and \(q\). The **Grashof condition** states that at least one link can make a complete revolution relative to the others if and only if

\[ s + l \le p + q. \]

When this holds the linkage is *Grashof* (Class I); when \(s+l > p+q\) it is *non-Grashof* (Class II) and no link can fully rotate, so every moving link merely rocks (a triple-rocker).

For a Grashof linkage the *inversion*, meaning which link is chosen as ground, selects the behavior. Grounding a link adjacent to the shortest link gives a **crank-rocker** (input rotates fully, output oscillates). Grounding the shortest link itself gives a **double-crank** or drag-link mechanism (both grounded links rotate fully). Grounding the link opposite the shortest gives a **double-rocker** (neither grounded link fully rotates, but the coupler makes a full turn). The special equality \(s+l = p+q\) is the *change-point* (or folding) case, where the links can become collinear and the output motion is momentarily indeterminate, which is usually avoided in practice.

<svg viewBox="0 0 260 130" width="260" height="130" stroke="currentColor" fill="none" stroke-width="2"><line x1="40" y1="110" x2="210" y2="110"/><circle cx="40" cy="110" r="4"/><circle cx="210" cy="110" r="4"/><line x1="40" y1="110" x2="70" y2="55"/><line x1="70" y1="55" x2="175" y2="40"/><line x1="175" y1="40" x2="210" y2="110"/><circle cx="70" cy="55" r="3"/><circle cx="175" cy="40" r="3"/><text x="22" y="124" font-size="11" stroke="none" fill="currentColor">O2</text><text x="205" y="124" font-size="11" stroke="none" fill="currentColor">O4</text><text x="48" y="85" font-size="10" stroke="none" fill="currentColor">crank</text><text x="105" y="38" font-size="10" stroke="none" fill="currentColor">coupler</text><text x="185" y="80" font-size="10" stroke="none" fill="currentColor">rocker</text></svg>

The four-bar matters because a huge range of tasks, including function generation (input angle mapped to a prescribed output angle), path generation (a coupler point tracing a target curve), and rigid-body guidance (moving a body through prescribed poses), can be realized with a single low-cost, low-friction, well-sealed loop of pin joints. Coupler-point curves in particular are remarkably rich, and much of classical mechanism synthesis is devoted to choosing link lengths so that a coupler point approximates a straight line, a dwell, or another desired trajectory.
