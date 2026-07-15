# gate-1.9: base primitives + twisted extrude (turned finial)

A turned finial / newel-post cap, the gate for bucket 1.9 (the third library-capability-audit
near-term pick: dress-up + base-feature completeness). Built on the real kernel; see
`tests/examples/test_gate_1_9.py`.

## Which feature each element exercises

- **`primitive` cylinder base** (`base`): a no-sketch base body (d30 x 8), the part's foundation.
- **twisted extrude shaft** (`shaft`): a 16 x 16 square profile extruded 40 mm with `twist = 90`
  (a 90-degree twist about the extrude axis), unioned onto the base.
- **`primitive` sphere cap** (`cap`): a d24 sphere elevated by `plane_offset = 48` so it seats atop
  the shaft, unioned above.
- **base-rim fillet** (`round`): a 2 mm fillet on the bottom edge; the radius is well under the
  base's `max_fillet` (the kernel validator that reports the largest feasible radius), so it always
  builds.

The four features fuse into one clean solid (a 30 x 30 x 60 mm turned ornament). The build is
deterministic and matches a golden geometry signature.

## Dropped / redundant (recorded for parity)

- The 3D **full-round fillet** ("Full Round Blend") is NOT built: build123d's `full_round` is a 2D
  sketch operation, and OCCT `BRepFilletAPI` is edge-fillet only, so a true full-round-blend is not
  available on the current stack (a commercial-kernel feature).
- Native `extrude_taper` is redundant with the existing `draft=` on `extrude` and was not added.
- 2D sketch fillet/chamfer already ship as sketch `modify: fillet`/`chamfer` ops.
