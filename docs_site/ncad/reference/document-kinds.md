# Document kinds

ncad is driven by authored text documents. There are eight kinds. Four of them (motion, physics,
analysis, drawing) are **overlays**: they reference another document and add only the semantics it
does not carry, so nothing is authored twice.

| Kind | Extension | Schema | Driving command |
| --- | --- | --- | --- |
| Part (feature tree) | `.hocon` / `.json` | `schema/part_schema.hocon` | `ncad build` |
| Assembly | `.asm.hocon` | `schema/assembly_schema.hocon` | `ncad assemble` |
| Motion study | `.motion.hocon` | validated programmatically | `ncad motion` |
| Physics / robot overlay | `.physics.hocon` | validated programmatically | `ncad physics` |
| Analysis (FEA) | `.analysis.hocon` | `schema/analysis_schema.hocon` | `ncad analyze` |
| Drawing (2D) | `.drawing.hocon` | validated programmatically | `ncad draw` |
| CAM slice profile | `.slice.json` | wrapper (slicer config) | `ncad slice` |
| Material library | `.hocon` | `schema/materials_schema.hocon` | (seed at `materials/seed.hocon`) |

## Top-level shapes

**Part** - `units`, `parts {}` (each part: `profile`, `material`, `connectors`, ordered `features`),
plus optional `parameters`, `datums`, `materials`, `materials_library`, `metadata`. See
[authoring parts](../guides/authoring-parts.md).

```properties
units = mm
parts { <name> { profile = solid, features = [ ... ] } }
```

**Assembly** - `units`, `assembly { instances, constraints, joints, couplings, expected_contact }`.
See [authoring assemblies](../guides/authoring-assemblies.md).

**Motion study** (overlay on an assembly) - `motion { assembly, driver{joint, from, to, steps},
outputs{traces, measures} }`. See [authoring motion](../guides/authoring-motion.md).

**Physics overlay** (overlay on an assembly) - `physics { assembly, base, joints{}, export{format,
mesh} }`; inertials are computed from geometry. An optional `srdf { groups, end_effectors,
group_states }` block adds planning semantics (emitted as a `.srdf` beside the urdf). See
[authoring robots](../guides/authoring-robots.md).

**Analysis** (overlay on a part) - `analysis { part, mesh, constraints[], loads[], steps[] }`. See
[authoring analyses](../guides/authoring-analyses.md).

**Drawing** (overlay on a part) - `drawing { part, sheet, views[], dimensions[], annotations[],
title_block }`; orthographic HLR views + selector-anchored dimensions to SVG + DXF. See
[authoring drawings](../guides/authoring-drawings.md).

**CAM slice profile** - a thin wrapper `{ config, slicers[], extra_args[] }` over an installed
slicer's own config, consumed by `ncad slice`.

**Material library** - a grouped bag (`physical`, `structural`, `thermal`, `appearance`) resolved from
the seed plus any document-inline `materials {}` and external `materials_library` file.

## Artifacts

Building a document writes to `out/<kind>/<name>/`. A part build emits `<name>.glb` (plus optional
step/stl/etc.) and sidecars (`.facts.json`, `.elementmap.json`, `.hierarchy.json`, `.status.json`,
`.bom.json`, `.plan.svg`, `.meta.json`, `.dfm.json`). An assembly writes `<name>.assembly.json`; a
motion study `<name>.motion.json`; a robot the `.urdf`/`.xml`/`.sdf` artifact (plus a `.srdf` planning
sidecar for a urdf) and `<name>.robot.json`; an analysis `<name>.analysis.json` plus a field mesh; a
drawing `<name>.drawing.svg` + `<name>.drawing.dxf`.
