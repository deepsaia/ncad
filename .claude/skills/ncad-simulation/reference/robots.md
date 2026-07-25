# Reference: authoring robots and physics

A physics overlay turns an assembly into a robot description (URDF / MJCF / SDF). Extension
`.physics.hocon`. Run with `ncad physics <doc>`. Link inertials are COMPUTED from the geometry, never
authored.

## Top-level shape

```properties
units = mm
physics {
  assembly = "<name>.asm.hocon"
  base = <instanceId>          # the root link (grounded)
  joints {                     # per-joint actuation overlay
    <jointId> { actuated = true, limit = [ lo, hi ], effort = .., velocity = .., damping = .. }
  }
  export { format = urdf, mesh = stl }   # format: urdf | mjcf | sdf
}
```

You supply only what the assembly does not carry: the base link, and per-joint actuation (actuated,
limits, effort, velocity, damping). Limits are in native units: radians for revolute, metres for
prismatic. Everything geometric, including inertia, is derived.

## Export formats and loop closures

| Format | Structure | Loops |
| --- | --- | --- |
| `urdf` | kinematic tree | drops loop-closing joints (reported) |
| `mjcf` | nested bodies | keeps loops as `<equality><connect>` |
| `sdf`  | flat | keeps every joint |

A closed-loop mechanism exports a clean tree in URDF with one joint dropped and noted, but a full
model in MJCF/SDF. An open serial chain exports cleanly in all three. Emitted URDF/MJCF is validated
by loading it in MuJoCo.

## Worked examples

Open chain (5-DoF desktop arm, five actuated joints):

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

```bash
ncad physics examples/08-robotics/desk_arm.physics.hocon --sweeps
```

Closed loop: `examples/08-robotics/crank_slider.physics.hocon` (one actuated revolute closes the
loop; URDF drops it, MJCF keeps it). An MJCF variant: `crank_slider_mjcf.physics.hocon`.

## Output and pitfalls

- Writes the robot artifact (`.urdf` / `.xml` / `.sdf`) + per-link meshes + the viewer
  `<name>.robot.json`; `--sweeps` adds per-joint articulation.
- `base` must be an instance id in the referenced assembly.
- For a closed loop, choose the export format deliberately (URDF drops a joint; MJCF/SDF keep all).
- Report which joints were dropped as loop closures; do not present a URDF as complete when it is not.
