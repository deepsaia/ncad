# gate-2.10: Phase 2 completeness (real parts)

Four real, recognizable parts exercise the bucket 2.10 features end to end (slow STEP
round-trip + determinism + golden signature in `tests/examples/test_gate_2_10.py`):

- **`hex_bolt.hocon`** - an M10 hex bolt (hex head + shank) with a **cosmetic thread**
  callout (the professional default, like NX/Creo/Fusion: metadata, no heavy geometry) drawn
  from the extended **ANSI/imperial hole-sizing table**.
- **`threaded_stud.hocon`** - a rod with a **modeled** (real helical) M10 thread, the explicit
  `modeled = true` opt-in (a V profile swept along a helix on the clean origin-axis cylinder).
- **`control_knob.hocon`** - a knob with **"ON" engraved on its curved side wall**
  (curved-surface wrap, assignable font with logged default fallback) and a chamfered top rim.
- **`shelf_bracket.hocon`** - the familiar L-shaped shelf support: a wall plate + arm joined
  into an L, a gusset rib bracing the corner, and a **datum plane** offset from the wall for a
  mounting-hole reference.

## Threads: cosmetic vs modeled (parity note)

Like NX/Creo/Fusion, the `thread` feature **defaults to cosmetic** (a callout such as
"M10x1.5" recorded as metadata, no geometry change) - light, robust, and all a machinist
needs. A **modeled** real-helix thread is an explicit opt-in (`modeled = true`) for when the
geometry itself is needed (STL/3D-print, mold tooling, renders); it is reliable on a clean
cylindrical stud about the origin axis and best-effort on composed geometry, because OCCT
thread booleans are fragile (the reason cosmetic is the default).
