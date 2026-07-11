# gate-3.5: per-body materials + derived mass

`materials_part.hocon`: a row of 3 patterned studs (part default `aluminium_6061`, nudged via
an inline `materials` override) plus a steel copy added by a `transform` (feature `material`
override). `lib/materials.hocon` is an external material library referenced by
`materials_library` (kept in a subdir so the `gate-*/*.hocon` sweep does not build it as a part).

Gate: each body reports mass = density x volume (density kg/m^3, volume mm^3, mass kg via the
1e-9 conversion); the assembly total mass/volume and mass-weighted COG are correct; and each
body's raw `mat_data` is queryable. Mass is computed on demand, never stored.
