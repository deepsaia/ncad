Facing generates a flat, clean reference surface by sweeping a face mill (or fly cutter) across the top of a raw blank in a set of overlapping parallel passes. It is almost always the first machining operation on a part, because a squared, known top face becomes the datum from which every subsequent depth, hole, and profile is measured. The operation removes a thin, uniform layer to eliminate mill scale, saw marks, and stock variation, and to bring the part to a controlled Z height.

The governing parameters are the radial stepover (width of engagement) \(a_e\), the axial depth of cut \(a_p\), and the feed per tooth \(f_z\). Passes are indexed sideways by \(a_e\), which for a face mill is set below the cutter diameter \(D\) so adjacent passes overlap; a practical range is \(a_e \approx 0.6\,D\) to \(0.8\,D\). Table feed follows from the tooth load and the number of effective teeth \(z\):
\[ v_f = f_z \, z \, n, \]
where \(n\) is spindle speed. A wider stepover clears faster but concentrates heat and raises cutting force per pass, so facing balances material-removal rate against tool life and surface flatness.

## Cutter engagement and entry
Where the cutter enters the material matters as much as the parameters. A face mill centered exactly on the edge of the stock produces the worst-case chip-thickness at entry and tends to chip inserts. Offsetting the spindle center to one side of the workpiece so the cutter is partially engaged (roughly two-thirds of the diameter) gives a favorable entry angle, keeps the chip thinning down as it enters and thickening as it exits, and mixes climb and conventional engagement in a controlled way. Multiple side-by-side passes are then indexed to cover the full width.

Surface finish from facing is dominated by the insert nose radius \(r_\epsilon\) and the feed. For a rounded nose the theoretical peak-to-valley and average roughness scale as
\[ R_z \approx \frac{f^2}{8\,r_\epsilon}, \qquad R_a \approx \frac{f^2}{32\,r_\epsilon}, \]
so a finishing face pass uses a low feed and often a wiper insert to leave a smooth, flat datum, while a roughing face pass maximizes removal and tolerates a coarser cusp between passes.
