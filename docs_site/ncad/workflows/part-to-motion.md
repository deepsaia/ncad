# Workflow: part to motion

Build a working mechanism from scratch: author the parts, compose them into an assembly, then drive
it with a motion study. We follow the crank-slider chain, which ships complete under
`examples/07-motion/`.

## 1. The parts

`crank_slider.hocon` defines the bodies as one part document (block, flywheel, rod, piston), each an
ordered feature tree. Each part declares the **connectors** (named coordinate frames) the assembly
will join: the flywheel's crank pin, the rod's two ends, the piston's wrist pin, the block's bore
axis. Build and inspect them:

```bash
ncad build examples/07-motion/crank_slider.hocon && ncad view
```

## 2. The assembly

`crank_slider.asm.hocon` instances those parts and joins them with lower-pair joints into a closed
loop (block to flywheel to rod to piston back to block). The joints keep the degrees of freedom the
mechanism needs (a revolute at each pin, a slider for the piston):

```bash
ncad assemble examples/07-motion/crank_slider.asm.hocon && ncad view
```

The solver reports the DoF state, so you know the loop is properly constrained (one input DoF).

## 3. The motion study

`crank_slider.motion.hocon` is a thin overlay: point at the assembly and sweep the flywheel joint one
revolution.

```properties
motion {
  assembly = "crank_slider.asm.hocon"
  driver = { joint = mainPin, from = 0, to = 360, steps = 72 }
}
```

```bash
ncad motion examples/07-motion/crank_slider.motion.hocon && ncad view
```

The multibody solver converges the loop at each step and produces the exact piston stroke, with no
per-mechanism formula. The result is the live trajectory:

<div class="ncad-viewer" data-ncad-model="../../../assets/models/crank_slider" data-ncad-motion="true"></div>

## The pattern

Each stage's output is the next stage's input, and nothing is authored twice: the parts carry
geometry and connectors, the assembly carries the joints, the motion study carries only the driver.
To take the same assembly further, overlay physics and export a robot
([assembly to robot](assembly-to-robot.md)).
