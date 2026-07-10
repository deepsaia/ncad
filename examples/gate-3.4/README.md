# gate-3.4: boolean upgrades + multibody algebra

- `multibody_algebra.hocon` part `split_block`: a 20x10x8 block split by the YZ plane
  (`keep = both`) -> 2 addressable bodies `halves/body/0` (+X side) + `halves/body/1`.
- part `multi_cut`: a 40x20x6 plate cut by three disjoint tool bodies in one
  `boolean operation = cut tools = [h1, h2, h3]` -> one drilled solid (multi-tool ref mode).
- part `scoped_merge`: a 3-body linear pattern (`row/body/0..2`) with a scope-mode
  `boolean operation = union scope = [row/body/0, row/body/2]` -> merges 0 and 2 into
  `merged/body/0`, leaves `row/body/1` addressable -> 2 bodies (multibody algebra).

Gate: all three build on the FakeKernel; the real kernel reproduces the golden signatures,
round-trips to STEP, and rebuilds deterministically.
