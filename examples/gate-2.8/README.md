# gate-2.8: hole wizard

- `counterbore_plate.hocon` - a 6mm hole with a 12x5 counterbore (socket-cap-screw).
- `countersink_plate.hocon` - a 6mm hole with a 12mm / 82-degree countersink (flat-head).
- `tapped_boss.hocon` - an M6 tap-drill hole (dia 5.0 via size+fit) with a cosmetic
  `thread = M6` tag.

All are slow STEP round-trips (see `tests/build/test_hole_wizard.py`).
