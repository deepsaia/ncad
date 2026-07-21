Grooving, threading, and parting are the specialized turning operations that use **form or plunge-oriented single-point tools** rather than the general profiling cutter, and each has distinctive kinematics on a lathe.

**Grooving** cuts a narrow recess, on an outside diameter, a face, or an internal bore, by feeding a tool of defined width radially (or axially) into the rotating part. Because a grooving insert engages on its full width at once, the radial force and chip evacuation are severe; wide grooves are therefore machined as a **series of overlapping plunges** across the groove width, sometimes with peck retracts to break and clear chips, rather than one full-width plunge. Grooving produces seal seats, retaining-ring grooves, undercuts for thread relief, and O-ring channels, so the width and corner radius of the tool directly define the feature.

**Threading** cuts a helix by synchronizing the tool's axial feed to the spindle rotation so that the tool advances exactly one **lead** per revolution:

\[ f_{\text{axial}} = L = n \cdot P, \]

where \(P\) is the pitch and \(n\) the number of starts. A thread is not cut in one pass; the full profile depth is reached over many passes, and the way successive passes bite is the key parameter. **Radial infeed** advances straight in and loads both flanks (simple but prone to chatter and poor chip control on coarse threads), whereas **flank (angled) infeed** advances along one flank so the chip forms on a single edge, greatly improving tool life and chip flow on larger pitches. The controller must also allow a run-up distance so the axis is synchronized and at speed before the thread form starts, and every pass must begin at the same angular spindle position (thread sync) or the starts will not align.

**Parting** (cut-off) severs the finished part from the bar by feeding a narrow blade radially all the way to the center. It is the most delicate turning operation because the blade is long, thin, and unsupported, and as it approaches the axis the surface speed \(v_c = \pi D N\) falls toward zero (rubbing rather than cutting) unless constant-surface-speed control raises \(N\), which itself is capped for safety near center. A small **pip** or burr often remains at the very center where speed vanishes.

## Common threads and constraints

All three operations share a dependence on rigid tooling and disciplined chip control because the tool is deeply engaged and poorly supported. Grooving and parting use similar blade-style tools and both risk the blade being dragged in (self-feeding) if feed and rigidity are wrong; threading shares the multi-pass, synchronized-feed discipline with any helical operation. In a turned-part program they typically follow the rough/finish/face sequence: profile the part, cut relief grooves, thread, then part off last so the workpiece stays supported by the bar for as long as possible.
