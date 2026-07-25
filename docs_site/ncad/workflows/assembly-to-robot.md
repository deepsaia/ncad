# Workflow: assembly to robot

Turn an existing assembly into a simulation-ready robot description. The physics overlay adds only
actuation; the link inertials are computed from the part geometry. We contrast an open chain and a
closed loop.

## Open chain: the desktop arm

`examples/08-robotics/desk_arm.asm.hocon` is a 5-DoF serial arm (base, turret, upper arm, forearm,
hand, sliding jaw). Its physics overlay names the base link and gives each joint actuation limits:

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
ncad view     # Physics mode: five live sliders + self-collision check
```

The arm is a base-rooted tree, so it exports a clean URDF with every joint. Inertia for each link
(mass, center of mass, tensor) is derived from the solids and their materials, never hand-typed.

## Closed loop: the crank-slider

`examples/08-robotics/crank_slider.physics.hocon` overlays the crank-slider, which is a closed loop.
The export format decides how the loop is handled:

```bash
ncad physics examples/08-robotics/crank_slider.physics.hocon                 # URDF: drops the loop joint (reported)
# edit export.format to mjcf to keep the loop as an <equality><connect>:
ncad physics examples/08-robotics/crank_slider_mjcf.physics.hocon            # MJCF: full model
```

URDF is a kinematic tree, so it drops the one loop-closing joint and reports it; MJCF and SDF keep
every joint. Emitted URDF/MJCF is validated by loading it in MuJoCo.

## Output

`ncad physics` writes the robot artifact (`.urdf` / `.xml` / `.sdf`) with per-link meshes, plus the
viewer sidecar `<name>.robot.json`. With `--sweeps` it also precomputes per-joint articulation for
the Physics viewer. See the [robots guide](../guides/authoring-robots.md) for the overlay vocabulary.
