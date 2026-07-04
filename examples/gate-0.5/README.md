# Gate 0.5: delete-a-feature, broken refs, and the TNP spike (closes Phase 0)

Proves the Phase 0 gate: a parameter edit or a feature delete/reorder yields a correct
incremental rebuild, and any reference that can no longer resolve is attributed to its
`id` (never silent garbage).

```bash
ncad build examples/gate-0.5/editable_bracket.hocon
ncad build examples/gate-0.5/two_body_clip.hocon
ncad
```

- `editable_bracket.hocon`: edit `thickness` and only the pad, holes, and fillet re-run
  (the sketch is a cache hit); the fillet's selector reference and the holes' generative
  `pad.cap(+Z)` reference both survive the edit. Delete the `pad` feature and the
  dependents report failure by their `id`, never silent garbage.
- `two_body_clip.hocon`: a plate with a unioned rail and a slot cut across it; the
  boolean and pocket name their inputs, so reordering one before its input is defined is
  rejected before any geometry runs by the dependency validator.
