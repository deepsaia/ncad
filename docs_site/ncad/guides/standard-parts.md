# Standard parts

ncad **generates** standard parts natively (no network, no import): give a family and a designation
and it emits a buildable ncad part document, then builds it. Command: `ncad spgen`. Every generated
part carries a provenance citation to the standard it follows.

```bash
ncad spgen <family> <designation>            # table lookup by designation
ncad spgen <family> --dim key=value ...      # custom dimensions (mm), bypassing the table
ncad spgen pipe_fitting <subtype> <designation>   # grouped families take a subtype
```

## Families

| Family | Standard | Example designations |
| --- | --- | --- |
| `washer` | ISO 7089 | `M3`, `M4`, `M5`, ... |
| `hex_nut` | ISO 4032 | `M3`, `M4`, `M5`, ... |
| `bearing` | ISO 15 (deep-groove) | `6000`, `6001`, `6002`, ... |
| `pipe` | EN 10220 | `DN15`, `DN20`, `DN25`, ... |
| `flange` | ASME B16.5 | `NPS1`, `NPS1.5`, `NPS2`, ... |
| `gasket` | ASME B16.21 | `NPS1`, `NPS1.5`, `NPS2`, ... |
| `i_beam` | Euronorm IPE | `IPE80`, `IPE100`, `IPE120`, ... |
| `pipe_fitting` | ASME B16.9 | subtypes `elbow` / `tee` / `reducer`, e.g. `DN25`, `DN40` |

## By designation

```bash
ncad spgen hex_nut M8
ncad spgen bearing 6002
ncad spgen pipe_fitting elbow DN50
```

Each writes a `<name>.hocon` part document and builds it to `out/parts/<name>/`, so the generated part
is a normal ncad document you can open, edit, or instance in an assembly like any other.

## Custom dimensions

When no table entry fits, pass explicit dimensions (mm) with `--dim`, which replaces the lookup:

```bash
ncad spgen washer --dim inner_d=8.4 --dim outer_d=16 --dim thickness=1.6
```

Use `ncad spgen <family>` with no designation to see the required dimension keys and the available
designations for that family. The generators are the platform for future families (profiles,
fittings, fasteners); the [Python API](../reference/python-api.md) exposes `StandardLibrary` for
programmatic generation.
