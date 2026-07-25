# Drive a motion study

A **motion study** drives a mechanism: it sweeps one joint's degree of freedom over a range and
re-solves the position network at each step, producing a trajectory. Couplings (gears, cams, belts)
make coupled joints follow. The document kind is a `.motion.hocon` overlay that references an
assembly and adds a driver.

We will drive the classic **crank-slider**: a flywheel turns a connecting rod that pushes a piston in
a block, converting rotation to reciprocating translation.

## The motion document

```properties
motion {
  assembly = "crank_slider.asm.hocon"
  driver = { joint = mainPin, from = 0, to = 360, steps = 72 }
}
```

That is the whole study: point at the assembly, name the joint to drive (`mainPin`, the flywheel
bearing), and sweep it one full revolution in 72 steps. ncad's multibody solver reproduces the exact
piston stroke from the declared joints alone, with no per-mechanism formula. One assembly can back
several studies (a different driver or range).

## Build it and watch

```bash
ncad motion examples/07-motion/crank_slider.motion.hocon
ncad view
```

`ncad motion` solves the trajectory and writes `out/assemblies/crank_slider/crank_slider.motion.json`
(a per-frame set of placements). In `ncad view`, the Motion mode plays it back on a timeline you can
scrub. It is the same data that drives the live scene below, which replays the solved trajectory
frame by frame (drag to orbit, scroll to zoom):

<div class="ncad-viewer" data-ncad-model="../../../assets/models/crank_slider" data-ncad-motion="true"></div>

## Where to go next

You have now built a part, composed an assembly, and driven a motion study. From here:

- The [authoring guides](../guides/authoring-parts.md) cover each document kind in depth (parts,
  assemblies, motion, robots, analyses, standard parts).
- The [workflows](../workflows/index.md) walk cross-cutting pipelines end to end (part to motion,
  assembly to robot, part to FEA, import to export).
- The [reference](../reference/cli.md) documents every CLI command, the HTTP API, the Python API, and
  the document kinds.
