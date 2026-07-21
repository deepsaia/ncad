Subtractive manufacturing shapes a part by removing material from an oversized blank (the *stock*) until only the desired solid remains. It is the dominant family for metal components that demand tight tolerance and fine surface finish, and it spans several distinct physical mechanisms: cutting with a **defined cutting edge** (milling, turning, drilling), cutting with a large population of **undefined abrasive grains** (grinding, honing, lapping), and **non-contact removal** such as electrical discharge machining (EDM), where controlled sparks erode a conductive workpiece submerged in a dielectric. What they share is a common logic: geometry is created by the *absence* of material, so every feature must be reachable and every removed region must have somewhere for the chip, grit, or debris to go.

In a process-planning model, a subtractive operation is best understood as a **profile applied over an already-built solid**. The finished B-rep is the reference; the plan reasons backward about how much stock to leave on each face, which surfaces a given tool and holder can physically reach, and in what order to peel away volume so that walls stay supported and the part remains rigid enough to hold tolerance. This is why order matters and why the finished shape alone does not define a manufacturing plan.

## Governing quantities

The throughput of a defined-edge cut is the **material removal rate**. For milling with radial width \(a_e\), axial depth \(a_p\), and table feed \(v_f\),

\[ \text{MRR} = a_e\, a_p\, v_f, \qquad v_f = f_z\, z\, n, \]

where \(f_z\) is feed per tooth, \(z\) the number of teeth, and \(n\) the spindle speed. Cutting force scales with the uncut chip cross-section through a material property, the **specific cutting energy** (or specific cutting pressure) \(k_c\): the tangential force is \(F_c = k_c\, A_c\) and the spindle power is \(P_c = F_c\, v\), with \(v\) the cutting speed. These relations let a planner trade depth, width, and feed against available torque, power, and the deflection budget of tool and part.

Tool wear sets an economic ceiling on speed. **Taylor's tool-life equation** captures the dominant trade-off,

\[ v\, T^{n} = C, \]

where \(T\) is tool life, and \(n\) and \(C\) are empirical constants for a given tool/work pair. Because \(n\) is small (roughly 0.1 to 0.3 for many metals), a modest speed increase collapses tool life dramatically, which is why cutting speed, not feed, is usually the first parameter constrained.

Subtractive processes excel where accuracy and finish dominate: micron-level tolerances, sharp internal features, and predictable material properties inherited directly from wrought stock. Their limitations are equally structural. Material is wasted as chips; deep pockets and internal cavities may be unreachable by any straight tool; and locally removing material relieves internal stress, so thin parts can distort after a heavy cut. A sound plan therefore couples geometry (reachability, access, tool length) with mechanics (force, deflection, residual stress) rather than treating them separately.
