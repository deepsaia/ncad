# Gate 6.0: driven mechanisms (motion spine)

The first Phase 6 (motion & kinematics) gate. A `motion` document (its own kind, like part /
assembly) drives one joint over a value sweep; the OndselSolver multibody engine (via the
`pyondsel` binding) solves the mechanism over time and writes a `<name>.motion.json` trajectory the
viewer's Motion tab plays back. Kinematic only (positions from geometry); force dynamics is
Phase 14.

## crank_slider

A single-cylinder crank-slider authored as a coarse PRIMITIVE BLOCKOUT (the motion authoring lane):
each part is a few primitives, and its mate points are named by COORDINATE (`at_point` / `axis`),
not by hunting faces. Four bodies:

- `block` (grounded): the machine frame - a base plate, a back wall (crankcase) carrying a bored
  BEARING BOSS the flywheel shaft turns in (`main`, axis Z), and a gusset holding the CYLINDER TUBE
  (`bore`, axis +Y) the piston slides in. So the flywheel is journalled in a real bearing and the
  cylinder is fixed to the same frame.
- `flywheel`: a disc whose hub extends into a shaft seated in the bearing boss; a crank-pin boss
  bridges forward at radius 20 (the crank throw R).
- `rod`: a diagonal connecting rod with BORED ring eyes that wrap the crank pin and the wrist pin
  with running clearance.
- `piston`: a slug with a forked slot the rod's small end rides in, spanned by the WRIST PIN
  (gudgeon pin) the rod pivots on.

Joints: 3 revolute (`mainPin`, `crankPin`, `wristPin`) + 1 slider (`slide`) in one closed kinematic
chain (block >> flywheel >> rod >> piston >> block cylinder). The `crank_slider.motion.hocon`
document drives the flywheel a full turn (`mainPin`, 0 to 360, 72 steps).

The point of the gate: ncad reproduces the closed-form piston stroke

```
yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2)   (R = crank radius 20, L = rod length 70)
```

from the DECLARED joints + one driver, with no per-mechanism formula anywhere in the engine. The
gate test asserts the mechanism assembles clash-free at rest (only the joints touch), the solved
piston position matches that analytic curve to within 1.0 mm at every one of the 73 frames, and the
piston reciprocates over a 40 mm stroke (top dead centre R + L = 90, bottom L - R = 50). Contrast
the hand-coded tbt-studio reference (`docs/images/crank-slider-reference.jpg`): there the stroke is
a typed-in equation; here it emerges from the joint graph.

## four_bar

Planned next (bucket 6.0 four-bar gate, task 94): a planar four-bar (crank-rocker) - ground + input
crank + coupler + output rocker, 4 revolute joints closing the loop, driven by the input crank. The
first CLOSED-LOOP gate: every frame must converge the loop. (The coupler-curve trace is bucket 6.1.)
