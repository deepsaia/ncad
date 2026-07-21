The **end-effector** is the device at the tip of a manipulator that acts on the world. **Grippers** grasp and hold objects; **tools** apply a process (welding, dispensing, deburring, machining). Because the end-effector determines what tasks a general-purpose arm can perform, its design is a discipline in itself, and quick-change couplings let one arm swap between several grippers and tools within a cycle.

## A taxonomy of prehension

Grippers are classified by the physics of how they retain a workpiece. **Impactive** grippers use jaws or fingers that clamp with mechanical force (parallel two-finger, angular, or multi-fingered hands). **Ingressive** devices penetrate the surface, as with pins or needles for textiles. **Astrictive** grippers hold by an attractive field without solid enclosure, chiefly **vacuum** suction cups and magnetic or electrostatic grippers. **Contigutive** grippers rely on direct contact adhesion (glue, surface tension, or gecko-like dry adhesion). The choice follows from part geometry, mass, surface finish, permeability, and the acceptable contact force.

## Grasp analysis: form and force closure

Whether a grasp actually secures an object is analyzed through the wrenches (force-torque pairs) that contacts can apply. Each contact contributes a set of admissible wrenches; stacking their bases forms the **grasp matrix** \(G\), so the net wrench on the object is \(w = G\,f\) for contact-force vector \(f\). A grasp achieves **force closure** when the contact wrenches positively span the entire wrench space, meaning any external disturbance wrench can be resisted by feasible (non-negative, friction-cone-respecting) contact forces:

\[ \forall\, w_{\text{ext}} \;\exists\, f \ge 0 : \; G\,f = -w_{\text{ext}}, \qquad f \in \text{friction cones}. \]

**Form closure** is the stronger, friction-independent condition in which the object is geometrically caged by the contacts and cannot move at all. Frictional force closure typically needs fewer contacts (three or four in the plane) than form closure, which is why compliant, high-friction fingertips are effective. Realistic contacts are modeled as point-with-friction (a linearized friction cone) or soft-finger contacts that also transmit a limited twisting moment.

## Tools, compliance, and interchange

Process tools shift the design emphasis from holding to controlled interaction. A welding torch or dispensing nozzle must maintain standoff and orientation along a path; a machining spindle or deburring tool must regulate contact force against surface variation. Deliberate **compliance**, whether passive (a remote-center-of-compliance mount that lets a peg self-align during insertion) or active (force-controlled about the tool contact), prevents jamming and excessive contact loads. Standardized tool-changer interfaces pass mechanical load, electrical signals, and pneumatic or hydraulic power across the coupling, so a single robot can carry the right end-effector for each stage of a task while preserving a known, repeatable tool reference frame.
