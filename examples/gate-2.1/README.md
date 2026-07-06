# Gate 2.1: Extrude/pocket end-conditions + draft + thin

Exercises the enriched extrude/pocket vocabulary: `blind`, `symmetric`, `two_side`,
`through_all`, `to_next`, `to_face`/`to_surface`, plus `draft` and `thin`.

- `end_conditions.hocon` , a base plate (blind), a symmetric drafted boss, and a
  through-all pocket, in one part. Builds deterministically and round-trips to STEP
  (bucket 2.0).

`end` defaults to `blind`, so a plain `{ distance = N }` extrude is unchanged.

Gate (2.1): a part mixing end-conditions builds and exports clean STEP.
