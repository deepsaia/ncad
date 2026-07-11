# gate-3.5: per-body materials + derived mass

`materials_part.hocon`: two spaced aluminium studs (a `pattern`, part default `aluminium_6061`
nudged via an inline `materials` override) plus a taller steel boss offset to the side, added
kept-separate by a `boolean union merge = false` with a `steel_1018` feature override. Three
distinct solids you can see apart in the viewport. `lib/materials.hocon` is an external material
library referenced by `materials_library` (kept in a subdir so the `gate-*/*.hocon` sweep does
not build it as a part).

Gate: each body reports mass = density x volume (density kg/m^3, volume mm^3, mass kg via the
1e-9 conversion); the assembly total mass/volume and mass-weighted COG are correct; and each
body's raw `mat_data` is queryable. Mass is computed on demand, never stored.
