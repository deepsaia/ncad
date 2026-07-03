# Gate 0.2: the everyday ops + expressions

Proves the parametric spine: parameters as expressions, plus the everyday op
vocabulary (sketch rectangle/circle/polygon, extrude, pocket, hole, fillet, chamfer,
boolean), built into solids and rendered.

```bash
ncad build examples/gate-0.2/bracket.hocon
ncad build examples/gate-0.2/hex_boss.hocon
ncad
```

- `bracket.hocon`: an 80 x 60 x 8 mm plate with four 6 mm corner holes placed via a
  `margin = hole_d * 1.5` expression, and rounded vertical edges (rectangle, extrude,
  hole, fillet).
- `hex_boss.hocon`: a concentric hexagonal flange with a round boss unioned on top and a
  square bore cut down the axis, top rim chamfered (polygon + circle sketches, extrude,
  boolean union, pocket, chamfer). Concentric by design: bucket 0.2 sketches all
  originate centered at z = 0, so off-axis and face placement wait for bucket 0.3.
