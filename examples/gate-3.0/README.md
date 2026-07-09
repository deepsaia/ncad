# gate-3.0: multibody foundation

- `two_body_bracket.hocon` - two disjoint extruded blocks kept as SEPARATE bodies by a
  keep-separate boolean union (`merge = false`). Each body is addressable with its own
  persistent id and volume; the part round-trips to STEP as a 2-solid assembly.

Proves the Phase 3 multibody foundation (bucket 3.0): first-class body identity, per-body
volume/signature, and multibody export. Slow determinism + STEP round-trip in
`tests/examples/test_gate_examples.py`.
