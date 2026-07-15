# gate-1.7: sketch solver completeness (rocker arm)

A symmetric rocker arm (a 2:1 lever pivoting about a central hole) whose profile is fully
constrained (dof 0) using the sketch-solver constraints added in bucket 1.7. It is the gate for the
first library-capability-audit near-term pick: the missing NX/Creo/Fusion/Onshape sketch relations
plus a solver-flexible cubic. Built on the real kernel; see `tests/examples/test_gate_1_7.py`.

## Which new constraint each feature exercises

- **symmetric_h** (symmetric about the horizontal centerline): the top/bottom point pairs
  (`lt`/`lb` and `re`/`rb`) mirror across y = 0, so the bar is symmetric top-to-bottom.
- **length_ratio**: the right arm (`rightTop`, pivot to right end) is 2x the left arm (`leftTop`),
  the defining 2:1 lever ratio.
- **point_line_distance**: the pivot sits 8 mm below the top edge (the bar's half-height), a
  perpendicular point-to-line dimension.
- **Solver-flexible 4-point bezier** (`blend`): the rounded right end is a cubic bezier whose free
  interior control point `bc1` is DRIVEN by a `tangent` constraint to the top edge (plus a distance
  from the end point), so the blend meets the top edge smoothly. This is the flexible control-point
  spline (py-slvs `addCubic` + `addCubicLineTangent`); it flexes in the solve rather than being a
  pinned point set.
- **points_vertical / collinear**: square ends (`re` above `rb`, `lt` above `lb`) and a straight top
  edge split at the pivot (`leftTop` collinear with `rightTop`).

The profile extrudes 6 mm and is pierced by a d10 pivot hole. The sketch solves well-constrained
(dof 0) and the built solid matches a golden geometry signature.
