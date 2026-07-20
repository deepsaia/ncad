A **wrap** projects a 2D profile, text or a sketch, onto a face and either raises it (**emboss**)
or recesses it (**engrave**) by a depth. It is how part numbers, logos, knurl patterns, and molded
lettering are applied to a surface.

## Emboss versus engrave

- **Emboss** adds material: the projected profile is extruded outward from the face by the depth, a
  raised logo.
- **Engrave** removes material: the profile is cut inward by the depth, a stamped serial number.

On a **flat** face the projection is a straightforward extrude in the face normal. On a **curved**
face (a cylinder or cone) the profile is projected onto the surface and thickened along the local
normal, so the text follows the curvature, wrapping around a bottle or a shaft.

## Text, fonts, and profiles

Text wrap takes a string, a font, and a style (regular/bold/italic); if the requested font is
missing the modeler falls back to a default and logs it, so the build stays deterministic rather
than silently substituting. A sketch-profile wrap uses any closed 2D geometry. Because wrap consumes
a face of the running solid, it comes after that face exists, and it references the face by a
persistent name so it stays attached through rebuilds.
