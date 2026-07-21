## Text, leaders, and item references

Beyond dimensions, a drawing carries annotations that communicate requirements not captured by geometry alone. Notes are text callouts: general notes apply to the whole drawing (material, finish, default tolerances, standards invoked), while local notes attach to a feature through a leader line ending in an arrowhead or dot. In an assembly drawing, balloons (item find-number references) are small circles containing an item number, connected by leaders to each component and keyed to a parts list so that every balloon number resolves to exactly one BOM row.

## Centerlines and line conventions

Drawings use a controlled alphabet of line types, each with a defined style and weight so that meaning stays unambiguous in monochrome. Visible edges are thick solid, hidden edges thin dashed, and centerlines a thin long-dash short-dash pattern marking axes of symmetry, bolt-circle centers, and paths of motion; a center mark is the small cross drawn at a circle's center. Phantom lines show adjacent parts or alternate positions, and break lines terminate broken views. Consistent line weight and style is what lets a reader instantly separate a real edge from an axis or a hidden feature.

## Hatching and symbolic callouts

Section lining (hatching) fills cut faces in section views with evenly spaced parallel lines, conventionally at 45 degrees; adjacent parts are hatched at different angles or spacings so their boundaries read, and pattern styles can code the material class. A family of standardized symbols carries dense engineering meaning compactly: surface-texture symbols specify roughness, welding symbols encode joint type and size on a reference line, and geometric-tolerancing feature control frames together with datum references state form, orientation, and position requirements. Because these symbols are ratified by standards, a feature control frame or a surface-finish callout means the same thing to any trained reader anywhere, which is the entire purpose of standardized annotation.
