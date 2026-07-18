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

A planar four-bar (crank-rocker): ground + input `crank` + `coupler` + output `rocker`, joined by 4
revolute joints in ONE CLOSED LOOP (ground >> crank >> coupler >> rocker >> ground). Like the
crank-slider it is a primitive blockout (each link is a bar + two bored ring eyes; the ground and
the joints carry pins the eyes ride, z-layered so nothing clashes). The `four_bar.motion.hocon`
drives the input crank (`pinA`) a full turn.

Geometry: A=(0,0), D=(90,0); crank 30, coupler 80, rocker 60. A Grashof crank-rocker (shortest 30 +
longest 90 = 120 <= 80 + 60 = 140), so the crank turns a FULL revolution while the rocker sweeps a
bounded ~60 deg arc. This is the first CLOSED-LOOP gate: the OndselSolver multibody engine (via
pyondsel) must CONVERGE the loop at every frame, not just walk a serial chain, all from the declared
joints + one driver.

The gate test asserts the mechanism assembles clash-free at rest, the closed loop stays closed
(the coupler's C pin and the rocker's C pin coincide to < 0.5 mm at all 73 frames), the rocker
oscillates over a bounded arc (a crank-rocker, not a full turn), and the solve is deterministic
across two runs. (A point on the coupler traces the classic coupler curve; that trace output is
bucket 6.1.)
