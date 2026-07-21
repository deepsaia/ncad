Once a stock-removal simulation has produced the as-machined in-process workpiece, the natural next question is how that simulated form differs from the intended design part. An **excess / remaining-material and gouge report** answers this by comparing the two solids and classifying every location on the design surface into one of three states: material left where it should have been cut (**excess** or **remaining**), material cut where it should have stayed (**gouge** or **overcut**), and surface that lies within an allowed tolerance band (**on-model**). It is the quantitative acceptance test that separates a merely plausible-looking toolpath from a correct one.

## The signed-distance idea

The governing quantity is a **signed distance** from a point on the reference part to the simulated stock surface. For a sample point \(\mathbf{p}\) on the design surface with outward unit normal \(\hat{\mathbf{n}}\), define the signed deviation along the normal to the machined surface:

\[
d(\mathbf{p}) = \left(\mathbf{q}^{*}-\mathbf{p}\right)\cdot\hat{\mathbf{n}}, \qquad \mathbf{q}^{*}=\arg\min_{\mathbf{q}\in\partial S_n}\lVert\mathbf{q}-\mathbf{p}\rVert .
\]

With the convention that \(\hat{\mathbf{n}}\) points away from the solid part, \(d>0\) means the machined stock stands *proud* of the design (uncut, remaining, or roughing allowance), and \(d<0\) means the stock has been cut *into* the design (a gouge). Classification then applies a two-sided tolerance: a point is on-model when \(-t_{\text{gouge}} \le d \le +t_{\text{excess}}\), excess when \(d > t_{\text{excess}}\), and a gouge when \(d < -t_{\text{gouge}}\). Gouge tolerances are typically far tighter than excess tolerances, because remaining stock can be removed by a later pass while removed material is unrecoverable.

## Sampling and computation

Measuring \(d\) everywhere is impractical, so the classic approach samples the design surface with a dense set of **points and surface normals** and casts each as a vector against the machined representation (or, symmetrically, samples the machined surface against the design). On a z-map or dexel structure this reduces to comparing stored depths along the sampling rays, which is fast and parallelizes trivially. The two dominant error sources are inherent to sampling: **discretization error**, set by sample spacing and grid resolution, and **chordal / faceting error** from approximating curved surfaces by facets. A defensible report states its resolution and tolerance bands so that a reported gouge of a few micrometers is not confused with a genuine cutter overcut.

## Reading the report and where it matters

Excess is not automatically a defect. On a roughing operation, a uniform positive \(d\) equal to the intended finishing stock is exactly correct; the report should confirm the allowance is present and even, not zero. Isolated pockets of excess flag **rest material** left by an oversized tool in corners and channels, which drives the choice of a smaller re-machining tool. Gouges, by contrast, are almost always faults: a mis-set tool length, an incorrect tool radius, an overrun at a path transition, or a collision that dragged the cutter into the wall. The same comparison also yields finish-quality metrics such as **scallop height** between adjacent passes. In short, the excess-and-gouge report closes the loop between the geometric ambition of the design and the physical reality the toolpath will produce, and it feeds decisions on tool selection, additional operations, and whether the program is safe to run at all.
