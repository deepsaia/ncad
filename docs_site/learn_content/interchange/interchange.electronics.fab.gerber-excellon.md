Gerber is the long-standing lingua franca for moving printed-circuit-board image data from design to fabrication. It is a 2D vector format: each physical layer of the board (each copper layer, the solder-mask openings, silkscreen legend, solder-paste stencil, board outline) is exported as its own monochrome image file, where "dark" means the presence of material or an opening and "clear" means its absence. The current format, historically called **RS-274X** or *extended Gerber*, replaced the obsolete RS-274D by embedding aperture (tool) definitions directly in the file instead of shipping them in a separate, easily-mismatched aperture list. **Excellon** is the companion numerical-control format that carries the drill and rout data (hole locations, tool diameters, plated vs. non-plated) for the NC machines that make the holes.

## The flash-and-draw model

A Gerber image is constructed from *apertures* -- named shapes such as a circle, rectangle, obround, or regular polygon. The plotter has two fundamental actions. A **flash** (operation code `D03`) stamps the current aperture once at a coordinate, which is how pads and via lands are drawn. A **draw** (operation `D01`) strokes the current aperture along a path, which is how copper tracks are drawn; a **move** (`D02`) repositions without exposing. Paths interpolate linearly (`G01`) or as circular arcs (`G02` clockwise, `G03` counter-clockwise), where an arc's center is given by signed `I`/`J` offsets from the current point. Filled areas such as copper pours are described in *region mode*: a closed contour opened with `G36` and closed with `G37` is filled solid. Complex custom pad shapes come from **aperture macros** (`AM`), which compose parametric primitives (lines, outlines, polygons, thermals, moirés) with per-primitive exposure on/off.

## Coordinates as fixed-point integers

Gerber coordinates are integers with an *implied* decimal point declared once by the format specification, for example `%FSLAX46Y46*%`: `L` = leading zeros omitted, `A` = absolute coordinates, and `X46`/`Y46` = four integer digits and six decimal digits. A raw coordinate integer \(N\) with \(d\) declared decimal digits therefore denotes

\[ \text{value} = \frac{N}{10^{\,d}} \]

in the unit set by the mode command `MO` (`MM` or `IN`). Thus with `X46` in millimetres the token `X2500000` means \(2.5\ \text{mm}\). Because the decimal point is implicit, the receiver must honor the exact `FS`/`MO` declaration; getting the digit counts or units wrong silently rescales the whole board.

<svg viewBox="0 0 320 90" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1.5">
  <text x="8" y="14" stroke="none" fill="currentColor" font-size="11">flash (D03): stamp aperture</text>
  <circle cx="30" cy="45" r="9"/>
  <circle cx="70" cy="45" r="9"/>
  <circle cx="110" cy="45" r="9"/>
  <text x="185" y="14" stroke="none" fill="currentColor" font-size="11">draw (D01): stroke a path</text>
  <line x1="195" y1="55" x2="245" y2="55"/>
  <line x1="245" y1="55" x2="245" y2="30"/>
  <line x1="245" y1="30" x2="300" y2="30"/>
</svg>

## From dumb pixels to intelligent metadata

Classic Gerber describes *only* geometry, which is why a design historically shipped as a loose "stack" of files (many Gerbers plus an Excellon file plus a separate netlist and bill of materials) with no enforced consistency between them. The **Gerber X2** revision addresses this by adding attributes: file attributes (`%TF`) declare a layer's function (e.g. top copper of a two-sided board), aperture attributes (`%TA`) declare what a shape is for (via pad, SMD pad, component lead), and object attributes (`%TO`) attach a net name or component reference designator to individual features. This layers machine-readable *meaning* on top of the image, letting downstream tools recover connectivity and function that previously had to be guessed.

## Excellon and its ambiguities

Excellon files begin with a header (`M48`) that declares units and a tool table (`T01C0.500` = tool 1, 0.5 mm), followed by a body that selects a tool and lists hole coordinates, with drilling (`G05`) and routing (`G00`/arc) modes. Excellon was never governed by a single rigorous standard, so its most notorious hazard is coordinate interpretation: whether leading or trailing zeros are suppressed, and the decimal format, must be communicated out-of-band or inferred, and a wrong guess shifts every hole. This fragility -- shared with the multi-file Gerber workflow -- is precisely why the industry has moved toward Gerber X2/X3 and the single-file intelligent formats for advanced boards, though Gerber plus Excellon remains the most widely accepted baseline that essentially every fabricator can consume.
