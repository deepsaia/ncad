# Gate 6.0: driven mechanisms (motion spine)

The first Phase 6 (motion & kinematics) gate. A `motion` block drives one joint over a value sweep;
the `PlanarMotionSolver` re-solves the mechanism at each step in a 2D workplane and writes a
`<name>.motion.json` trajectory the viewer's Motion tab plays back. Kinematic only (positions from
geometry); force dynamics is Phase 14.

## crank_slider

A single-cylinder crank-slider: ground `frame`, `crank` web, connecting `rod`, and `piston`, joined
by 3 revolute joints + 1 slider in one closed kinematic chain (frame >> crank >> rod >> piston >>
frame slideway). The `motion` block drives the crank a full turn (`mainPin`, 0 to 360, 72 steps).

The point of the gate: ncad reproduces the closed-form piston stroke

```
yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2)   (R = crank radius 20, L = rod length 70)
```

from the DECLARED joints + one driver, with no per-mechanism formula anywhere in the engine. The
gate test asserts the solved piston position matches that analytic curve to within 0.5 mm at every
one of the 73 frames, and that the piston reciprocates over a 40 mm stroke (top dead centre R + L =
90, bottom L - R = 50). Contrast the hand-coded tbt-studio reference
(`docs/images/crank-slider-reference.jpg`): there the stroke is a typed-in equation; here it emerges
from the joint graph.

Parts are cut from flat plate (every bore parallel to +Z, the mechanism-plane normal), so the
mechanism is planar and the solver works in a single 2D workplane, which is how SolveSpace / NX /
Creo solve linkages robustly (a closed planar loop is ill-conditioned as stacked 3D lower pairs).

## four_bar

A planar four-bar (crank-rocker): ground + input crank + coupler + output rocker, 4 revolute joints
closing the loop, driven by the input crank. It is the first CLOSED-LOOP gate: every frame must
converge the loop. The gate asserts every frame solves and the output rocker sweeps a bounded,
non-trivial arc as the input crank turns. (The coupler-curve trace is bucket 6.1.)
