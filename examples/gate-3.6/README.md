# gate-3.6: Phase 3 capstone - flanged shaft coupling

A flanged shaft coupling that composes the Phase 3 capabilities in one believable part:

- **Bolt-circle** (circular pattern of cut features): a cutter cylinder placed at the bolt
  radius (`circle at = [22, 0]`), circular-patterned `count = 6, merge = false`, then
  boolean-cut from the flange -> 6 bolt holes.
- **Mirror**: the half-coupling is mirrored across its base plane into a symmetric two-flange
  coupling.
- **Multibody + materials**: an `aluminium_6061` flange and a `steel_1018` hub, kept as
  separate addressable bodies (`boolean union merge = false`, feature material override), so
  per-body mass properties report aluminium vs steel with a correct assembly total. After the
  mirror: 4 bodies (2 flanges + 2 hubs).
- Central + hub bores cut through the axis.

Gate: builds clean on the FakeKernel; the real kernel reproduces the golden per-body signature
and mass properties, round-trips to STEP, rebuilds deterministically, and composes additively.

This part surfaced (and this bucket fixed) three multibody correctness gaps: a `circle at`
center offset (a patterned origin-circle would stack at the axis), flattening BodySet operands
in boolean cut, and preserving per-body provenance/material through keep-separate union + mirror.
