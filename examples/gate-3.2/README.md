# gate-3.2: feature-level body patterns (linear + circular)

Two body patterns exercised end to end:

- `patterned_bodies.hocon` part `pattern_studs`: a 6x6x10 stud replicated on a 4x3 linear
  grid, kept separate (`merge = false`) -> 12 bodies with born-once ordinal ids
  `grid/body/0..11`. Demonstrates keep-separate multibody output and stable instance
  identity (foundational-risk R2).
- `patterned_bodies.hocon` part `spoke_hub`: a spoke crossing the axis, replicated 6 times
  about +Z through the origin and fused (`merge = true`) -> one valid 6-spoke solid.
  Demonstrates the circular kind and a fused single-solid result.

Gate: both parts build cleanly on the FakeKernel; the real kernel reproduces the golden
per-body / single-body signatures, round-trips to STEP, rebuilds deterministically, and
the fused `spoke_hub` composes additively (each feature prefix is one valid solid).
