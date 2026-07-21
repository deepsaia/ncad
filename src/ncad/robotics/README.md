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

The `export.format` in the overlay selects the writer (`robot_format.robot_writer`):

- **`UrdfWriter`** (`format = urdf`): URDF is a kinematic TREE. `JointTreeSpanner` roots the joint
  graph at the base link; a loop-closing joint (e.g. a four-bar) is reported and excluded (URDF
  cannot express it). Artifact `.urdf`.
- **`MjcfWriter`** (`format = mjcf`): MuJoCo's native format, the best simulation target. Nests each
  child body inside its parent (BodyTree), writes the full inertia tensor (`fullinertia`), declares
  mesh assets, KEEPS every loop-closure joint as an `<equality><connect>`, and adds a `<position>`
  actuator per actuated joint. Artifact `.xml`.
- **`SdfWriter`** (`format = sdf`): Gazebo's format, the middle ground. Flat links + joints like
  URDF but NOT tree-limited, so every joint (including loop closures) is emitted. Artifact `.sdf`.

All three write from the shared `RobotModel` IR. Emitted URDF and MJCF are validated by loading them
in MuJoCo (`mujoco.MjModel.from_xml_path`); MJCF preserves closed-loop mechanisms a URDF must drop.

## Viewer sidecars (Physics mode)

Alongside the export artifact, `ncad physics` can write viewer sidecars for the Physics mode
(`RobotSidecarBuilder`). These are OPTIONAL: the cheap tree rides on `--sidecars` (default on); the
expensive per-joint sweeps only on `--sweeps` (a motion solve per actuated joint). `--no-sidecars`
writes just the export artifact.

- **`<name>.robot.json`**: the tree the inspector reads - base link, links (mesh + computed
  mass/COM/inertia), joints (type/parent/child/origin/axis/limit, `actuated`, `loop_closure`).
- **`<name>.robot_sweeps.json`**: per ACTUATED revolute/slider joint, a precomputed sweep of
  per-body placements produced by driving that joint across its range with the OndselSolver motion
  path (so closed loops move correctly). A viewer slider scrubs its joint's frames - one joint at a
  time (the precompute tradeoff; live multi-joint posing would need browser forward kinematics).

Sweep range: authored `[lower, upper]`; a continuous revolute sweeps one full turn; an unlimited
prismatic sweeps an auto travel from the model size. Each sweep solves in a throwaway temp dir, so
the output dir gets only the two robot sidecars (no per-joint churn). Missing pyondsel is handled
honestly: the tree still writes, sweeps are skipped with a note. The viewer's Physics view mode
(auto-generated joint sliders + tree/inertial inspector) reads these sidecars.
