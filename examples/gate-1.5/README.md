# Gate 1.5: Sketch status in the viewer (Phase 1 gate)

Surfaces each sketch's constraint status (well/under/over/inconsistent + dof + failing
constraint ids) in the viewer (a collapsible status badge in the sidebar) and the CLI
(a per-sketch status line), via a `<stem>.status.json` sidecar written at build time.

- `underconstrained_tab.hocon` , a tab left under-constrained (one corner fixed, sides
  horizontal/vertical, but no size dimension, so width/height are free). It still solves
  and builds a face, and its status sidecar reports `under` with the free DoF. Covers the
  gate's "an under-constrained sketch solves or reports cleanly".

The **over-constrained** case is covered by a unit/build test (it produces no shape but
reports its status cleanly). The **fully-constrained-drives-a-feature** half of the gate
is the existing gate-1.3 `constrained_bracket` (a dof-0 profile driving an extrude).

Gate (Phase 1): an over/under-constrained sketch solves or reports cleanly; a
fully-constrained profile drives a downstream feature.
