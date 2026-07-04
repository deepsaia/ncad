# Gate 0.4: incremental rebuild & determinism

Proves the cached, dependency-aware executor: a parameter edit re-executes only the
dirty suffix, the same document rebuilds deterministically, and geometry equality is
the section-4a topology-signature + toleranced-measures definition (not BREP bytes).

These parts add no new ops over gate 0.3; they are deliberately **parameter-rich** so
that editing one value in the viewer and rebuilding shows the incremental behaviour.

```bash
ncad build examples/gate-0.4/param_plate.hocon
ncad build examples/gate-0.4/param_standoff.hocon
ncad build examples/gate-0.4/param_bar.hocon
ncad
```

- `param_plate.hocon`: a parametric plate with four corner holes on the top cap and
  rounded vertical edges. Edit `fillet_r` and only `soften` re-runs; edit `thickness`
  and the sketch is a cache hit while the pad, holes, and fillet re-run.
- `param_standoff.hocon`: a square base with a unioned cylindrical boss and an axial
  through-bore, top rim chamfered. Edit `bore_d` and only the bore pocket (and the
  chamfer after it) re-run; edit `base_w` and the base branch re-runs while the boss
  sketch stays cached.
- `param_bar.hocon`: a slotted bar whose central pocket tracks the bar size via a
  `wall` expression. Small and quick, so it shows the deterministic-rebuild half of the
  gate (same document, identical signature) as clearly as the incremental half.
