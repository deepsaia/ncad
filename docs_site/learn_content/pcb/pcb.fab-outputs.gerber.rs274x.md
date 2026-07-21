The **Gerber format** is the long-standing lingua franca for handing a finished printed-circuit design to a fabricator. A board is not a single object to a fab shop; it is a *stack of 2-D images* -- one per copper layer, plus solder mask, silkscreen, paste stencil, and the board outline. Gerber encodes each of these as its own file. The modern dialect, **RS-274X** ("extended Gerber", also written X1, with the attribute-carrying successor **X2**), replaced the obsolete RS-274-D. The crucial difference is that X *embeds the aperture definitions inside the file itself*, whereas the old D-code format required a separate, easily-mismatched "aperture wheel" description. This single change eliminated the most common class of fabrication error and is why RS-274-D is considered deprecated.

## The imaging model

A Gerber layer is built from just two primitive operations acting on a set of named **apertures** (shapes such as circles, rectangles, or arbitrary polygons defined by *aperture macros*): a **draw**, which sweeps an aperture along a path to make a track, and a **flash**, which stamps an aperture at a coordinate to make a pad. The photoplotter (or its modern raster equivalent) reproduces exactly this sequence. Coordinates are stored as scaled integers under a declared *format specification*; a header token such as `%FSLAX46Y46*%` says each coordinate has 4 integer and 6 decimal digits, so a stored value \(N\) maps to a physical coordinate

\[ v = N \times 10^{-d}, \qquad d = 6. \]

Getting \(d\), the unit (inch or millimetre), and the zero-suppression convention right is essential: a decimal-place error silently scales the entire board.

## Drilling: the Excellon companion

Gerber describes *images*, not *holes*. Holes and routed slots are carried in a separate **Excellon** file (named for the NC drilling machines whose control language it borrows). An Excellon file is a small tool table -- each tool given a diameter -- followed by a list of tool selections and \((x, y)\) hit coordinates, optionally with plated/non-plated distinction and rout (G-code-like) commands for slots. Because drill data lives in its own file with its own coordinate header, alignment between the drill origin and the Gerber origin is a classic integration checkpoint.

## Why it matters, and what is displacing it

Gerber's strength is universality: essentially every fabricator on earth can consume it, and it is deliberately simple and vector-exact. Its weakness is that a design arrives as a *pile of loosely-coupled files* with no intrinsic netlist, stackup, or bill of materials, so a fab must re-derive intent (which files are which layer, what the drill map means) from filenames and convention. This motivated richer single-archive successors -- **ODB++** and **IPC-2581** -- that bundle imagery, drill, stackup, netlist, and assembly data together with explicit semantics. In a mechanical-CAD workflow, generating Gerber/Excellon is typically *delegated* to the specialist ECAD tool that owns the copper design rather than re-implemented, since the format's correctness depends on the same tool that authored the traces and pads.
