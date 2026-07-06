# Gate 1.4d: Sketch-modify split + whole-loop offset

Completes the sketch-modify family: `split`, line-arc/arc-arc corner fillet/chamfer, and
whole-loop `loop_offset` (a `TopologyApplier` pre-solve op built on a shared
`EntityOffsetter`).

- `offset_frame.hocon` , a rectangle loop offset inward by 4 with mitred corners becomes
  a smaller rectangle face. Satisfies the gate.
- `rounded_offset.hocon` , the same offset with `corner = round`, a smaller
  rounded-rectangle face (tangent fillet arcs of radius = |distance|).

`loop_offset` replaces the source loop (single-loop); a concentric ring / face-with-hole
is deferred multi-loop work. A negative distance insets (shrinks) the loop regardless of
the authored winding.

Gate: a rectangular loop offset inward with mitred corners builds a smaller face.
