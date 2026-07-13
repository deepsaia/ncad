# gate-1.6: conic + text sketch entities

Two real parts prove the remaining 1.6 sketch entities end to end (slow STEP round-trip +
determinism + golden signature in `tests/examples/test_gate_1_6.py`):

- **`nameplate.hocon`** - a machine nameplate: a rectangular plate with the raised text
  "NCAD" unioned onto its top face. Proves the **text** sketch element and **multi-loop
  faces** (the counters in "A"/"D" are real inner-loop holes).
- **`guitar_pick.hocon`** - a guitar pick (rounded triangle): three corner points joined by
  three **conic** edges (rho 0.55) whose apex points bulge each side outward. Proves the
  conic entity (rho model: one conic tool, rho selecting the ellipse/parabola/hyperbola
  family, built as a rational quadratic Bezier), matching how NX/Creo/Fusion expose conics.

Both build with well-constrained (dof 0) sketches. See `docs/plan.md` for the full 1.6 scope
(ellipse family + arc_polar shipped in 1.6a; conic, smooth G1 continuity, ellipse
minor-radius dimension, and sketch reference geometry are the rest of 1.6).
