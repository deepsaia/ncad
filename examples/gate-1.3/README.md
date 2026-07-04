# Gate 1.3: the full constraint vocabulary + dimensions

Proves the complete sketch constraint set (parallel, perpendicular, tangent, equal,
symmetric, midpoint, point-on-entity, collinear, concentric, fix) and dimensional
constraints (angle, diameter; radius shipped in 1.2), plus driven-vs-driving dimensions
(a driven dimension is measured from the solved geometry, not enforced).

```bash
ncad build examples/gate-1.3/constrained_bracket.hocon
ncad build examples/gate-1.3/tangent_bar.hocon
ncad
```

- `constrained_bracket.hocon`: a fully-constrained plate (one corner fixed, sides
  horizontal/vertical, width + height dimensioned) that solves to dof 0, no
  under-constrained warning. The concrete proof that a fully-constrained profile drives
  a feature.
- `tangent_bar.hocon`: a stadium bar whose arc caps are tangent to the straight sides,
  fixed and dimensioned, with a driven (reference) dimension `span` that measures the
  overall width and reads back without constraining it.
