# Reference: authoring drawings

A `.drawing.hocon` is an overlay on a built part. Run with `ncad draw`.

## Top-level shape

```properties
drawing {
  part = "<part>.hocon"                          # the model to draw
  sheet = { size = A3, orientation = landscape } # A4 | A3 | A2 | A1
  views = [ ... ]
  dimensions = [ ... ]
  annotations = [ ... ]
  title_block = { title = "...", drawn_by = "...", scale = "1:1" }
}
```

## Views

Each view is projected via OCCT hidden-line removal (visible edges solid, hidden dashed):

- **base** - projects onto a named plane. `projection = XY` (top), `XZ` (front), `YZ` (right).
- **projected** - derives from a parent base view + a relative `direction` (`up` / `down` / `left` /
  `right`), third-angle. Its `from` must name an existing view.
- **iso** - an isometric pictorial.

```properties
views = [
  { id = front, type = base, projection = XZ, at = [ 70, 120 ] }
  { id = top,   type = projected, from = front, direction = up, at = [ 70, 60 ] }
  { id = right, type = projected, from = front, direction = right, at = [ 200, 120 ] }
  { id = iso,   type = iso, at = [ 320, 80 ] }
]
```

`at` is the view origin on the sheet (mm).

## Dimensions

Reference model geometry by selector; the drafting layer projects the matched edges into the view and
measures them. Types: `linear`, `diameter`, `radius`.

```properties
dimensions = [
  { view = front, type = linear,
    between = "select edges where length > 4.9 and length < 5.1 and mid_x > 5.5 and mid_x < 6.5 and mid_z < 40" }
]
```

- A `linear` dimension measures the span between the FIRST TWO matched edges, so the selector must
  isolate exactly the intended pair. Combine attributes (`length`, `mid_x`, `mid_y`, `mid_z`,
  `orientation`) to pin them.
- `diameter` / `radius` use `of = "select edges where ..."` on a circular edge.
- A selector matching no geometry -> the dimension is skipped with a warning.

## Worked example

`examples/11-drafting/shelf_bracket.drawing.hocon`: front/top/right + iso views and a linear
dimension resolving to a clean 22 mm gap up the wall plate.

```bash
ncad draw examples/11-drafting/shelf_bracket.drawing.hocon
```

## Pitfalls

- The part must build first; the drawing references a built part.
- Broad selectors measure the wrong edges. Verify the value in the output and tighten the selector.
- The SVG is deterministic; the DXF is not byte-reproducible (the format embeds a per-write
  fingerprint + timestamp). Compare DXF by entities, not bytes.
