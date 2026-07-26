# Authoring drawings (2D)

A **drawing** turns a built part into a 2D engineering drawing: orthographic views via hidden-line
removal (HLR), placed on a sheet, with dimensions and annotations, emitted as **SVG** (for viewing)
and **DXF** (for CAM / laser / CNC handoff). Extension: `.drawing.hocon`. Run with `ncad draw`. It is
an overlay: it references a built part and adds only the sheet + views + dimensions.

## Top-level shape

```properties
drawing {
  part = "shelf_bracket.hocon"           # the model to draw (a built part)
  sheet = { size = A3, orientation = landscape }   # A4 | A3 | A2 | A1
  views = [ ... ]
  dimensions = [ ... ]
  annotations = [ ... ]
  title_block = { title = "...", drawn_by = "...", scale = "1:1" }
}
```

## Views

Each view projects the model onto the sheet via OCCT hidden-line removal (visible edges solid, hidden
edges dashed):

- **base** - projects onto a named plane. `projection = XY` (top), `XZ` (front), `YZ` (right). The
  view direction is that plane's normal.
- **projected** - derives its direction from a parent base view plus a relative `direction`
  (`up` / `down` / `left` / `right`), so front / top / right stay coherent (third-angle).
- **iso** - an isometric pictorial (looks along a body diagonal).

```properties
views = [
  { id = front, type = base, projection = XZ, at = [ 70, 120 ] }
  { id = top,   type = projected, from = front, direction = up, at = [ 70, 60 ] }
  { id = right, type = projected, from = front, direction = right, at = [ 200, 120 ] }
  { id = iso,   type = iso, at = [ 320, 80 ] }
]
```

`at` is the view origin on the sheet (mm). A `projected` view's `from` must name an existing view.

## Dimensions

A dimension references **model geometry via a selector** (not raw coordinates), so it survives a
rebuild: the drafting layer resolves the selector against the part's element map, projects the
matched edges into the view, and measures the projected geometry.

```properties
dimensions = [
  { view = front, type = linear,
    between = "select edges where length > 4.9 and length < 5.1 and mid_x > 5.5 and mid_x < 6.5 and mid_z < 40" }
]
```

Types: `linear` (distance between two selected features), `diameter` and `radius` (of a selected
circular edge). Write the selector so it isolates the intended edge(s); a `linear` dimension measures
the span between the first two matched edges. If a selector matches no geometry, the dimension is
skipped with a warning.

## Annotations and title block

```properties
annotations = [ { view = front, at = [ 20, 20 ], text = "MATL: steel_1018" } ]
title_block = { title = "Shelf Bracket", drawn_by = "ncad", scale = "1:1" }
```

## Build it

```bash
ncad draw examples/11-drafting/shelf_bracket.drawing.hocon            # SVG + DXF
ncad draw examples/11-drafting/shelf_bracket.drawing.hocon -f svg     # SVG only
```

Artifacts land in `out/drawings/<name>/`: `<name>.drawing.svg` (open in any browser) and
`<name>.drawing.dxf`. The DXF places visible edges on a `VISIBLE` layer and hidden edges on a dashed
`HIDDEN` layer, ready for a CAM / laser / CNC toolchain.

## Pitfalls

- **Selectors must isolate the intended edges.** A broad selector matches many edges and a `linear`
  dimension then measures the wrong pair; combine attributes (`length`, `mid_x`, `mid_z`,
  `orientation`) to pin the exact edges.
- **DXF is not byte-reproducible** (the format embeds a per-write fingerprint + timestamp); the SVG
  is deterministic for the same model + document.
- Drawings pair with a URDF-style exact model; sections, detail views, GD&T, and BOM tables are not
  in this first drafting increment.
