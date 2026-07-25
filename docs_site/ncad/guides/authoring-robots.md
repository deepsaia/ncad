# Authoring robots and physics

A **physics overlay** turns an assembly into a robot description (URDF, MJCF, or SDF). Extension:
`.physics.hocon`. Built with `ncad physics`. It is an overlay on an assembly, and its defining trait
is that **link inertials are computed from the part geometry, never authored** (mass, center of mass,
and the full inertia tensor come from the solids and their materials).

```properties
units = mm
physics {
  assembly = "<name>.asm.hocon"
  base = <instanceId>          # the root link (grounded)
  joints {                     # per-joint actuation overlay
    <jointId> { actuated = true, limit = [ lo, hi ], effort = .., velocity = .., damping = .. }
  }
  export { format = urdf, mesh = stl }   # urdf | mjcf | sdf
}
```

## The overlay

You supply only what the assembly does not carry: which instance is the base link, and per-joint
actuation properties (whether a joint is actuated, its limits, effort, velocity, damping). Limits are
in the export's native units: radians for revolute joints, metres for prismatic. Everything
geometric, including inertia, is derived.

## Export formats and loop closures

The three writers differ in how they handle a kinematic loop:

| Format | Structure | Loops |
| --- | --- | --- |
| `urdf` | kinematic tree | drops loop-closing joints (reported) |
| `mjcf` | nested bodies | keeps loops as `<equality><connect>` constraints |
| `sdf`  | flat | keeps every joint |

So a closed-loop mechanism (like the crank-slider) exports a clean tree in URDF with one joint
dropped and noted, but a full model in MJCF/SDF. An open serial chain (an arm) exports cleanly in all
three. Emitted URDF/MJCF is validated by loading it in MuJoCo.

## Two examples

An **open chain** (`examples/08-robotics/desk_arm.physics.hocon`): a 5-DoF desktop arm, every joint
in the base-rooted tree, five actuated joints, so the viewer shows five live forward-kinematics
sliders:

```properties
physics {
  assembly = "desk_arm.asm.hocon"
  base = base
  joints {
    base_yaw { actuated = true, limit = [ -3.14159, 3.14159 ], effort = 40, velocity = 3.14, damping = 0.1 }
    shoulder { actuated = true, limit = [ -1.65806, 1.65806 ], effort = 60, velocity = 2.0,  damping = 0.2 }
    elbow    { actuated = true, limit = [ -2.09439, 2.09439 ], effort = 40, velocity = 2.5,  damping = 0.15 }
    wrist    { actuated = true, limit = [ -2.09439, 2.09439 ], effort = 15, velocity = 3.0,  damping = 0.05 }
    grip     { actuated = true, limit = [ -0.024, 0.0 ],       effort = 20, velocity = 0.1,  damping = 0.05 }
  }
  export { format = urdf, mesh = stl }
}
```

A **closed loop** (`examples/08-robotics/crank_slider.physics.hocon`): one actuated revolute closes
the loop, so URDF drops it (reported) while MJCF keeps it.

## Build it

```bash
ncad physics examples/08-robotics/desk_arm.physics.hocon --sweeps
```

This writes the robot artifact (`.urdf` / `.xml` / `.sdf`) with per-link meshes, plus the viewer
sidecar `<name>.robot.json` (links + computed inertia + joints). `--sweeps` also precomputes
per-actuated-joint articulation for the Physics viewer mode, which shows the live sliders and a
self-collision check at each pose. See the [assembly-to-robot workflow](../workflows/assembly-to-robot.md).
