# gate-1.6a: ellipse family + arc_polar

Two parts prove the 1.6a sketch entities end to end (slow STEP round-trip + determinism +
golden signature in `tests/examples/test_gate_1_6a.py`):

- **`luggage_tag.hocon`** - a luggage tag: an `ellipse` outline (major radius 30, minor
  radius 18) extruded to a 3mm plate, with a round strap hole (an `arc_polar` top semicircle
  + a plain arc bottom semicircle) boolean-cut through it near one end.
- **`elliptical_flange.hocon`** - an ellipse plate with a round hub unioned on top (an
  `arc_polar` top semicircle + a plain arc bottom semicircle).

## What it exercises

- **ellipse** (and, downstream, the point-carries-DoF model): the ellipse is defined by a
  center point + a major-axis-end point (which carry the solver DoF, since py-slvs has no
  ellipse primitive) plus a `minor_radius`; the analytic curve is derived by the kernel via
  `build123d.Edge.make_ellipse`. A full ellipse is a lone closed loop (like a circle).
- **arc_polar** authoring sugar: `center` / `radius` / `start_angle` / `sweep` is lowered by
  `EntityExpander` into a three-point arc. Its two derived endpoints are emitted as **fixed**
  primitives, so an arc_polar is well-constrained by construction (dof 0) with only its
  center pinned; the generated endpoint ids (`<id>/start`, `<id>/end`) are reused by an
  adjacent arc to close a full circle.
