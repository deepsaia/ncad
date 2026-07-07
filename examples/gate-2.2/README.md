# Gate 2.2: Revolve / groove

Exercises the revolve (additive) and groove (subtractive) sketched features. A profile is
revolved about an axis into a solid of revolution.

- `revolved_washer.hocon` , an offset rectangular profile revolved 360 about the Y axis
  into a washer, then a shallow groove revolved and cut around it. Builds deterministically
  and round-trips to STEP (bucket 2.0).

Axis can be `X`/`Y`/`Z`, or `{ point = [...], dir = [...] }` for an arbitrary axis anywhere
in space. `angle` (default 360) makes a partial revolve; `symmetric` centers the arc;
`thin` revolves a wall.

Gate (2.2): a revolved part + a groove builds and exports clean STEP.
