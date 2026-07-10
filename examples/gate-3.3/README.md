# gate-3.3: mirror (reflect a body across a plane)

Two body mirrors exercised end to end:

- `mirrored_bodies.hocon` part `symmetric_bracket`: an L-shaped half-model whose upright lies
  on the YZ plane, mirrored across YZ and fused (`keep = true, merge = true`) -> one symmetric
  solid. Demonstrates the common "finish the symmetric part" flow and single-solid validity
  (planar contact at x = 0).
- `mirrored_bodies.hocon` part `mirror_pair`: a boss offset from the plane, mirrored across YZ
  kept separate (`merge = false`) -> 2 addressable bodies `pair/body/0` (original) +
  `pair/body/1` (reflection). Demonstrates addressable mirror instances.

Gate: both parts build cleanly on the FakeKernel; the real kernel reproduces the golden
single-solid / per-body signatures, round-trips to STEP, rebuilds deterministically, and the
fused `symmetric_bracket` composes additively (each feature prefix is one valid solid).
