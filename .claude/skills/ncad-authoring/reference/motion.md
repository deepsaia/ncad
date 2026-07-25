# Reference: authoring motion

A motion study drives a mechanism and produces a trajectory. Extension `.motion.hocon`. Run with
`ncad motion <doc>`. It is an overlay: it references an assembly and adds a driver + optional outputs.

## Top-level shape

```properties
motion {
  assembly = "<name>.asm.hocon"
  driver = { joint = <jointId>, from = 0, to = 360, steps = 72 }
  outputs {
    traces = [ ... ]      # point paths over the sweep (optional)
    measures = [ ... ]    # time-series scalars over the sweep (optional)
  }
}
```

## The driver

Sweeps ONE joint's DoF from `from` to `to` in `steps` increments. At each step the multibody solver
(OndselSolver via pyondsel) re-solves the whole position network, converging closed loops. No
per-mechanism formula: the trajectory follows from the declared joints and couplings. One assembly
can back several studies (different driver joint or range).

## Couplings propagate the driver

If the assembly declares couplings (gear, cam, belt, rack_pinion, scotch_yoke, geneva, universal),
the driven joint propagates through them, so one driver turns a whole gear train or lifts a cam
follower. Mobility (Gruebler-Kutzbach + the solver's actual free-DoF) is reported; per-frame
interference events are flagged.

## Outputs

- A `trace` records a point's path over the sweep (a coupler curve, an output locus).
- A `measure` records a scalar per frame: `coordinate`, `distance`, or `angle`.

```properties
outputs {
  measures = [
    { id = lift, kind = coordinate, instance = follower, point = [ 0, 20, 0 ], axis = y }
  ]
}
```

## Worked examples

Slider-crank (one closed loop, rotation to reciprocation):

```properties
motion {
  assembly = "crank_slider.asm.hocon"
  driver = { joint = mainPin, from = 0, to = 360, steps = 72 }
}
```

```bash
ncad motion examples/07-motion/crank_slider.motion.hocon && ncad view
```

Cam-follower with a lift measure: `examples/07-motion/cam_follower.motion.hocon`. The example set also
has four_bar, gear_pair, planetary, geneva, rack_pinion, scotch_yoke, walking_beam,
reciprocating_pump, peaucellier, each a small overlay on its `.asm.hocon`.

## Pitfalls

- The `joint` in the driver must be an actual joint id in the referenced assembly, and it must be
  drivable (a joint with a free DoF); otherwise the build reports `driver_joint_missing` /
  `driver_joint_not_drivable`.
- More `steps` means a smoother trajectory but a longer solve.
- To export the mechanism as a physics robot instead, use the ncad-simulation skill.
