Constant-scallop finishing (also called constant-cusp, or steepness/flat-adaptive finishing) generates 3D passes whose spacing is varied point by point so that the residual ridge left between neighboring passes, the **scallop**, stays at a fixed height everywhere on the surface. It is the theoretically optimal single-tool finishing strategy for freeform surfaces: for a chosen finish tolerance it removes as little redundant material and travels as short a path as any raster or waterline scheme can, because no region is machined tighter than the specification requires.

The controlling relationship is the ball-nose cusp equation. For a tool of radius \(r\) and a stepover \(s\) measured **across the actual surface**, the scallop height is

\[ h = r - \sqrt{r^2 - \left(\tfrac{s}{2}\right)^2}, \qquad\text{so}\qquad s = 2\sqrt{2rh - h^2}. \]

A raster path holds a constant stepover in the XY plane, so on a wall of slope \(\theta\) the surface stepover becomes \(s_{\text{surf}} = s_{xy}/\sin\theta\) and the scallop balloons on steep faces; waterline holds constant \(\Delta z\) and does the opposite, exploding on flats. Constant-scallop instead solves for the stepover as a function of local slope so that \(s_{\text{surf}}\) itself is held constant, giving uniform \(h\) across the whole part regardless of orientation.

The usual construction is **geodesic offsetting**: starting from a seed curve on the surface (often the steepest or a boundary contour), the next pass is placed at a constant geodesic distance \(s\) along the surface, then the next, and so on. Because geodesic distance follows the true surface metric rather than a projection, the passes naturally converge on steep areas and diverge on flat ones by exactly the amount needed to keep the cusp fixed. Robust generators compute this on a distance field or mesh, handling saddles, islands, and self-approaching offset fronts where the offset curve would collide with itself.

## Steepness classification

In practice constant-scallop is frequently deployed as part of a **steep/shallow (steepness) split**: a slope threshold partitions the model into steep regions, finished with a Z-level/waterline pass, and shallow regions, finished with a constant-scallop (or 3D-offset) pass, with the two blended along the boundary. This hybrid keeps each strategy in the regime where it is well conditioned and avoids the degenerate spacing each suffers at the extremes. The single scallop-height parameter then becomes the one knob that trades surface finish against cycle time across the entire part.
