Parallel (raster) finishing is a 3D strategy for finishing sculptured surfaces with a ball-nose cutter. The toolpath is built from a family of equally spaced parallel vertical planes; each plane intersects the part surface in a curve, and the tool follows those curves in turn, so in plan view the passes are straight parallel lines while in space they ride up and down over the geometry. The XY stepover between passes is constant, which makes the strategy simple, predictable, and efficient to compute and to cut.

Because a round-nosed tool cannot fill the valley between two adjacent passes, it leaves a small ridge, the scallop or cusp, whose height controls the surface finish. On a locally flat, horizontal surface, a ball of radius \(r\) stepped over by \(s\) leaves a cusp of height
\[ h = r - \sqrt{r^{2} - \left(\tfrac{s}{2}\right)^{2}}, \]
which inverts to let the planner choose a stepover for a target cusp:
\[ s = 2\sqrt{2\,r\,h - h^{2}}. \]
A smaller stepover or a larger ball radius reduces the cusp at the cost of more passes and longer cycle time, so finishing is a direct trade between surface quality and machining time.

## Slope dependence and where it fits
The crucial limitation is that a constant XY stepover does not give a constant cusp on sloped surfaces. On a wall inclined at angle \(\beta\) to horizontal, the spacing measured along the surface is \(s/\cos\beta\) (it grows as the wall steepens), so the cusp swells on steep regions and the finish degrades; in the limit of a vertical wall the parallel planes graze it and leave essentially unmachined bands. Parallel finishing is therefore best on shallow, gently varying surfaces. Steep regions are better finished by constant-Z (waterline) passes or by a constant-scallop strategy that adapts spacing to slope, and a common workflow combines a parallel pass on the flats with a waterline pass on the walls. Direction can be single-way (all passes climb-milling for consistent finish) or zig-zag (faster, but alternating cut direction can leave a visibly directional pattern).

<svg viewBox="0 0 200 90" width="200" height="90" stroke="currentColor" fill="none" stroke-width="1.5"><path d="M10 70 A18 18 0 0 1 46 70"/><path d="M46 70 A18 18 0 0 1 82 70"/><path d="M82 70 A18 18 0 0 1 118 70"/><line x1="28" y1="70" x2="28" y2="20" stroke-dasharray="2 2"/><line x1="64" y1="70" x2="64" y2="20" stroke-dasharray="2 2"/><path d="M28 63 L46 63" /><path d="M46 58 L46 63"/><text x="120" y="40" font-size="9" fill="currentColor" stroke="none">cusp h between</text><text x="120" y="52" font-size="9" fill="currentColor" stroke="none">passes at stepover s</text></svg>

*Adjacent ball-nose passes leave a residual cusp of height h.*
