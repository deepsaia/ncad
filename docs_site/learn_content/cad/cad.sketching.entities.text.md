Sketch text is a first-class sketch entity: a run of characters positioned in the sketch plane whose glyph shapes are resolved into ordinary sketch geometry (lines and curves forming closed contours), rather than being stored as a cosmetic annotation. It exists so that lettering (part numbers, serial marks, dial legends, logos, gauge graduations, mold cavity markings) can participate in the parametric feature tree as real geometry. Because the resolved outlines are genuine profiles, downstream features can extrude them into raised lettering (emboss), cut them into recessed lettering (engrave or deboss), wrap them onto a cylindrical or freeform face, or use them as trim and split tools. This distinguishes sketch text from drawing/annotation text, which lives on a drawing sheet, carries no volume, and never becomes solid geometry.

## From glyphs to sketch curves

The governing idea is *font outline decomposition*. A digital font stores each glyph (each character shape) as one or more closed contours built from on-curve and off-curve control points. TrueType outlines use quadratic Bézier segments; PostScript/CFF outlines (as carried in the OpenType container) use cubic Bézier segments; both may include straight line segments. The modeler reads the font file, extracts the glyph contours, and reconstructs each contour as a chain of sketch primitives. A quadratic segment is

\[ \mathbf{B}(t) = (1-t)^2\,\mathbf{P}_0 + 2(1-t)t\,\mathbf{P}_1 + t^2\,\mathbf{P}_2, \qquad t \in [0,1], \]

and a cubic segment adds a control point,

\[ \mathbf{B}(t) = (1-t)^3\,\mathbf{P}_0 + 3(1-t)^2 t\,\mathbf{P}_1 + 3(1-t)t^2\,\mathbf{P}_2 + t^3\,\mathbf{P}_3. \]

Glyph coordinates are expressed in *font units* on an em square whose resolution is declared by the font (commonly 1000 units per em for CFF outlines, 2048 for TrueType). To place the text at a requested nominal size the modeler applies a uniform scale

\[ s = \frac{\text{size}}{\text{unitsPerEm}}, \]

mapping font units into model units before the contours are emitted into the sketch.

## Holes, winding, and fill

Many glyphs enclose interior voids: the counters of "O", "A", "e", or "8". These are represented as separate contours whose orientation (clockwise versus counter-clockwise) is opposite to the enclosing outer contour. A fill rule, typically the nonzero winding rule (an alternative is even-odd), classifies each region as material or void by counting signed crossings of a test ray. Correct orientation is what lets an extrude leave the counter of an "O" open instead of filling it. A small diagram of one contour with its on-curve endpoints (circles) and an off-curve control point (square) makes the reconstruction concrete:

<svg viewBox="0 0 240 120" width="240" height="120" stroke="currentColor" fill="none" stroke-width="1.5">
  <path d="M20 100 Q120 -10 220 100" />
  <line x1="20" y1="100" x2="120" y2="20" stroke-dasharray="4 4" />
  <line x1="120" y1="20" x2="220" y2="100" stroke-dasharray="4 4" />
  <circle cx="20" cy="100" r="4" />
  <circle cx="220" cy="100" r="4" />
  <rect x="116" y="16" width="8" height="8" />
  <text x="14" y="116" font-size="10" stroke="none" fill="currentColor">P0</text>
  <text x="210" y="116" font-size="10" stroke="none" fill="currentColor">P2</text>
  <text x="128" y="20" font-size="10" stroke="none" fill="currentColor">P1 (off-curve)</text>
</svg>

## Layout, alignment, and text on a path

Beyond individual glyphs, the entity performs typographic layout. Glyphs are set along a baseline using each glyph's *advance width*, with optional *kerning* adjustments for specific character pairs and overall *tracking* (letter spacing). Horizontal alignment (left, center, right) and vertical reference (baseline, cap height, mean line) position the whole run relative to an anchor placed in the sketch. Many implementations also support *text on a curve*: each glyph origin is parameterized along a guide curve, and the glyph is rotated to the curve's tangent so lettering follows an arc or spline. Because these are governed by sketch constraints and dimensions, the anchor, size, and path can all be driven parametrically.

## Parametrics, robustness, and where it matters

As a parametric entity, the string content, font, style, size, and spacing can be model variables, and the rebuild regenerates the outlines on each recompute. This raises practical robustness concerns. Font substitution must be deterministic and logged: if the specified font is unavailable, a documented fallback keeps rebuilds reproducible rather than silently changing geometry. Real-world fonts occasionally produce self-intersecting, overlapping, or degenerate contours (from hinting artifacts or careless authoring) that a solid kernel will reject, so healing/cleanup of the outlines is often required before extrusion. Very small text or thin serifs create tiny edges that can break tessellation or thin-wall extrudes, and the identity of the resulting edges and faces should be stable so downstream selections survive edits. These capabilities matter wherever geometry must carry legible marks: nameplates and control-panel legends, embossed or engraved logos, casting and forging identification, injection-mold cavity text, medical-device markings, and traceability codes (serials, lot numbers) that are integral to the part rather than applied afterward.
