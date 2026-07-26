---
name: ncad-drafting
description: >-
  Author and produce 2D engineering drawings from a built ncad part: orthographic HLR views
  (front/top/right/iso), selector-anchored dimensions, and annotations on a sheet, emitted as SVG
  (viewing) and DXF (CAM / laser / CNC handoff). Use when the user wants a drawing, a 2D view, a
  dimensioned print, or a DXF for cutting. For 3D parts, assemblies, or motion, use the
  ncad-authoring skill; for robots or FEA, use ncad-simulation.
---

# Authoring ncad drawings (2D)

A drawing turns a built part into a 2D engineering drawing: orthographic views via hidden-line
removal, dimensions, and annotations on a sheet. The document kind is a `.drawing.hocon` overlay;
`ncad draw` emits SVG (for viewing) and DXF (for a CAM / laser / CNC toolchain).

## When to use

- The user wants a **drawing / print / 2D views** of a part (front, top, right, isometric).
- The user wants a **dimensioned** drawing.
- The user wants a **DXF** for laser / waterjet / CNC / plotting.

For authoring the 3D part itself, assemblies, or motion, use **ncad-authoring**; for robot export or
FEA, use **ncad-simulation**.

## The workflow

1. **Make sure the part builds** first (`ncad build <part>`); a drawing references a built part.
2. **Author the `.drawing.hocon`** overlay (see `reference/drawings.md`): pick the sheet, the views,
   and the selector-anchored dimensions.
3. **Run `ncad draw`** and read the output paths + any warnings.
4. **Check the result** and iterate. ALWAYS run `ncad draw` and report what it wrote / warned; never
   claim a drawing without producing it. A dimension whose selector matches no geometry is skipped
   with a warning, so tighten the selector when you see that.

## Command

```bash
ncad draw <doc.drawing.hocon>            # SVG + DXF into out/drawings/<name>/
ncad draw <doc.drawing.hocon> -f svg     # SVG only  (-f svg,dxf is the default)
```

Artifacts: `out/drawings/<name>/<name>.drawing.svg` (open in any browser) and `<name>.drawing.dxf`
(VISIBLE + dashed HIDDEN layers, ready for CAM). See `reference/dxf-handoff.md` for the DXF layer
conventions.

## Principles

- **Dimensions reference model geometry via selectors** (`select edges where ...`), not raw
  coordinates, so they survive a rebuild. Write the selector to isolate the intended edge(s): a
  `linear` dimension measures the span between the first two matched edges.
- **Verify, do not assume.** Report the SVG/DXF paths `ncad draw` returns and any skipped-dimension
  warnings.
- **Accurate scope.** Base / projected / iso views + linear / diameter / radius dimensions ship;
  sections, detail views, GD&T, and BOM tables do not yet. Do not offer them.

Deep reference: the live docs guide at
https://deepsaia.github.io/ncad/ncad/guides/authoring-drawings/.
