# Robotics export

Derive a robot/physics description from an ncad assembly. `ncad physics <doc.physics.hocon>` reads a
physics overlay, builds the referenced assembly, and writes a robot description (URDF today) plus a
per-link mesh for each body.

## The `.physics.hocon` overlay

A physics document is an OVERLAY on an assembly, not a standalone robot (mirrors how
`.motion.hocon` overlays an assembly with a driver). It references the assembly and adds only the
robot/sim semantics the assembly does not know:

```hocon
physics {
  assembly = "../07-motion/crank_slider.asm.hocon"
  base = block                                  # the root link
  joints {
    mainPin { actuated = true, limit = [ -3.14, 3.14 ], effort = 50, velocity = 6.28, damping = 0.05 }
  }
  export { format = urdf, mesh = stl }
}
```

## Derived vs authored

The key property: inertia is COMPUTED, never typed (most tools, and text-to-cad's hand-written
`gen_urdf()`, make you enter it).

| Derived from the built assembly | Authored in the overlay |
|---------------------------------|--------------------------|
| link mass / COM / inertia tensor (MassCalculator, the B3 tensor) | which joints are actuated |
| per-link mesh (Stage-0 STL export) | joint limits + effort/velocity |
| joint parent/child, origin, axis (assembly joints + connector frames) | joint dynamics (damping/friction) |
| kinematic-tree spanning + loop detection | the base (root) link, export target |

## Pipeline

`RobotModelBuilder` produces a format-neutral `RobotModel` (links + joints, SI units) from the
assembly + overlay; a format writer serializes it. The IR is written once so writers stay thin.

- **`UrdfWriter`** (now): URDF is a kinematic TREE. `JointTreeSpanner` roots the joint graph at the
  base link; a joint that closes a loop (e.g. a four-bar) is reported and excluded (URDF cannot
  express it). Emitted URDF is validated by loading it in MuJoCo (`mujoco.MjModel.from_xml_path`).
- **`MjcfWriter` / `SdfWriter`** (follow-ups on the same IR): MJCF keeps closed loops as equality
  constraints and adds actuators/contacts; SDF is the middle ground. See the backlog.

A viewer Physics tab (joint-slider articulation of the exported robot) is deferred to the B12
viewer-parity work; it should follow the MJCF writer so it can articulate closed-loop mechanisms.
