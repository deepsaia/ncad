# Gate 1.4b: Sketch-modify transforms

Demonstrates the transform family of sketch-modify operations (a `TransformApplier`
pre-solve stage): `move`, `rotate`, `scale`, `mirror`, and `pattern` (linear/circular).

- `mirrored_profile.hocon` , a half-profile mirrored across an axis welds into one
  closed symmetric loop and extrudes to a solid. Points on the mirror axis map onto
  themselves, so the two halves stay welded. Builds on both the FakeKernel gate sweep
  and the real kernel.
- `linear_pattern.hocon` , a linear pattern replicates a closed square four times along
  X. The copies are disjoint loops, so this is verified at the entity level.
- `circular_pattern.hocon` , a circular pattern replicates a round hole six times about
  the origin (a bolt circle). Also disjoint loops, verified at the entity level.

A multi-loop face is deferred until `WireOrderer` supports multiple loops, so the two
pattern examples are excluded from the FakeKernel "builds without issues" sweep and have
their own targeted entity-level tests.

Gate: a mirrored half-profile builds a closed face; a linear/circular pattern replicates
entities (multi-loop face deferred).
