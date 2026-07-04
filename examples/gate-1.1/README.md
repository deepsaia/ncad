# Gate 1.1: the constraint solver + first constrained sketch

Proves the solver seam: a sketch authored as explicit 2D entities (points + lines) and
constraints (horizontal, vertical, coincident, distance) is solved by py-slvs
(SolveSpace) to positions, closed into a wire, and extruded. DoF / conflict status is
reported as id-tagged issues (an under-constrained but buildable sketch is a warning,
not an error).

```bash
ncad build examples/gate-1.1/constrained_rect.hocon
ncad build examples/gate-1.1/constrained_lbracket.hocon
ncad
```

- `constrained_rect.hocon`: a rectangle as 4 points + 4 lines made rectangular by
  horizontal/vertical constraints and sized by two distances, the "hello world" of the
  solver next to the primitive rectangle form.
- `constrained_lbracket.hocon`: an L-shaped profile as 6 constrained line segments, a
  shape that cannot be a centered primitive and needs the solver.
