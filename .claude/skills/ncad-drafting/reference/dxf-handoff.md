# Reference: DXF handoff (CAM / laser / CNC)

`ncad draw` emits `out/drawings/<name>/<name>.drawing.dxf` alongside the SVG. DXF is the interchange
format a CAM / laser / waterjet / CNC / plotter toolchain consumes.

## Layers

The drawing is organized on named DXF layers so a downstream tool can filter what it cuts:

| Layer | Contents | Linetype |
| --- | --- | --- |
| `VISIBLE` | visible view edges (the profile to cut / plot) | solid |
| `HIDDEN` | occluded edges (reference only, not cut) | dashed |
| `DIMENSIONS` | dimension lines + value text | solid |
| `ANNOTATIONS` | annotation text + the title-block rectangle | solid |

For a laser / waterjet cut, the tool typically imports the `VISIBLE` layer as the cut path and
ignores `HIDDEN` / `DIMENSIONS` / `ANNOTATIONS`.

## Geometry conventions

- Coordinates are in millimetres, y-up (DXF's native frame; no flip, unlike the SVG).
- Straight edges are `LWPOLYLINE` entities; dimension lines are `LINE`; text is `TEXT`.
- Each view is placed at its `at` origin on the sheet, so a multi-view drawing lays the views out on
  one DXF as they appear on the sheet.

## Choosing formats

```bash
ncad draw <doc.drawing.hocon>            # both SVG + DXF (default)
ncad draw <doc.drawing.hocon> -f dxf     # DXF only, for a pure cutting handoff
```

## Reproducibility note

The DXF container embeds a per-write fingerprint GUID + a version-and-timestamp string, so two writes
of the same drawing are not byte-identical. The DRAWING (the entities, layers, geometry) is
deterministic. If you diff or golden a DXF, compare parsed entities, not raw bytes; the SVG is
byte-deterministic if you need an exact comparison.
