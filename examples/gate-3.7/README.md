# gate-3.7: Phase 3 completeness (real parts)

Three real, recognizable parts exercise the bucket 3.7 features (slow STEP round-trip +
golden signature in `tests/examples/test_gate_3_7.py`):

- **`bolt_circle_flange.hocon`** - a pipe flange with a central bore and a bolt circle of 8
  holes with **2 suppressed** (a clocking gap). Exercises the **circular pattern +
  per-instance suppress**: one bolt-hole cutter is patterned to 8 positions, ordinals 0 and 4
  dropped, then cut.
- **`pin_heatsink.hocon`** - a pin-grid heat sink: a base pad with an upstanding pin,
  **fill-patterned** across the pad's top face into a field of ~35 cooling pins on one base.
- **`bimetal_bushing.hocon`** - a bronze inner liner in a steel outer shell, kept as **two
  addressable bodies with distinct materials** (drives the By-Material view, the per-body
  **inertia tensor**, and the baked per-body glTF colors).

## Notes on the replication model (parity)

- **Fill / body patterns replicate the RUNNING solid** over one of its own faces; a distinct
  cutter over a distinct part's face is a FEATURE pattern (re-running a feature at transformed
  locations), which is moved to Phase 4 (it needs a feature-replay engine).
- **Split by tool body** partitions the running solid into inside/outside regions; `split`
  mints both regions under one feature, so a single `material` cannot color them separately
  (per-region material on split is a follow-up). A true bi-material part is built as two
  bodies, each under its own feature so each carries its own material (see the bushing).
- Per-body **appearance colors** are written into the exported glTF (baseColorFactor), so the
  bushing's steel/bronze colors port to any renderer, not just the ncad viewer.
