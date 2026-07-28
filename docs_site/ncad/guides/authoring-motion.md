# Authoring motion

A **motion study** drives a mechanism and produces a trajectory. Extension: `.motion.hocon`. Built
with `ncad motion`. It is an overlay: it references an assembly and adds only a driver and optional
outputs.

```properties
motion {
  assembly = "<name>.asm.hocon"
  driver = { joint = <jointId>, from = 0, to = 360, steps = 72 }
  outputs {
    traces = [ ... ]      # point paths traced over the sweep (optional)
    measures = [ ... ]    # time-series scalars over the sweep (optional)
  }
}
```

## The driver

The driver sweeps ONE joint's degree of freedom from `from` to `to` in `steps` increments. At each
step the multibody solver (OndselSolver, via `pyondsel`) re-solves the whole position network,
converging closed loops. There is no per-mechanism formula: the trajectory follows from the declared
joints and couplings alone.

```properties
motion {
  assembly = "crank_slider.asm.hocon"
  driver = { joint = mainPin, from = 0, to = 360, steps = 72 }
}
```

One assembly can back several studies (a different driver joint or range).

## Couplings drive coupled joints

If the assembly declares couplings (gear, cam, belt, rack_pinion, scotch_yoke, geneva, universal),
the driven joint propagates through them, so a single driver turns a whole gear train or lifts a cam
follower. A coupling is enforced as a **prescribed** relation: the solver drives the coupled joint by
the declared ratio or profile (`output = f(driver)`), rather than simulating tooth mesh or cam
contact, so the ratio you author is the ratio you get. The mechanism's mobility is reported as a
planar Gruebler-Kutzbach count (planar mechanisms) alongside the solver's actual free-DoF, and
per-frame interference events are flagged.

Couplings **chain**: a coupling enforces when its first `between` joint is already driven, whether
directly by the driver or by an upstream gear/belt coupling's output. So a multi-stage gear train
runs from one input, composing cumulative ratios (stage 2's ratio multiplies stage 1's), and the
listing order does not matter. Only gear and belt outputs chain onward (a linear angular ratio);
a rack slide, cam, geneva, or scotch-yoke output is a leaf (it cannot be the primary of a further
angular coupling). A coupling whose primary is never driven is simply left unenforced.

## Outputs: traces and measures

- A **trace** records a point's path over the sweep (a coupler curve, an output-point locus).
- A **measure** records a scalar per frame: a coordinate, a distance, or an angle.

```properties
outputs {
  measures = [
    { id = lift, kind = coordinate, instance = follower, point = [ 0, 20, 0 ], axis = y }
  ]
}
```

That measure reports the cam follower's lift: flat through the dwell, rising to the nose and back.

## Build it and watch

```bash
ncad motion examples/07-motion/cam_follower.motion.hocon && ncad view
```

`ncad motion` writes `<name>.motion.json` (per-frame placements + any traces/measures). In `ncad
view`, the Motion mode scrubs the trajectory on a timeline. The live scene here replays the solved
crank-slider trajectory the same way:

<div class="ncad-viewer" data-ncad-model="../../../assets/models/crank_slider" data-ncad-motion="true"></div>

## The example set

`examples/07-motion/` has a study per mechanism kind: `crank_slider` (slider-crank), `four_bar`
(closed loop), `cam_follower` (cam), `gear_pair` and `planetary` (gears), `geneva` (intermittent),
`rack_pinion`, `scotch_yoke`, `walking_beam`, `reciprocating_pump`, `peaucellier` (straight-line
linkage). Each is a small overlay on its `.asm.hocon`. To export a mechanism as a physics robot, see
[authoring robots](authoring-robots.md).
