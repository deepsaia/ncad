Rest machining, also called remaining-stock or reference-tool roughing, machines only the material that a previous operation could not reach, rather than reprocessing the whole part. It works by comparing two representations of stock, the **in-process stock model** left by the prior tool and the desired target shape, and generating a toolpath confined to the difference between them. A smaller (or differently shaped) tool then removes just those leftover regions: the corners a large roughing cutter could not enter, the shallow bands a steep pass skipped, and the residual steps between roughing levels.

The governing concept is the **in-process workpiece (IPW)** or stock update. After each operation the CAM system carries forward a model, commonly a voxel grid, a dexel/z-map, or a boolean B-rep, of exactly what material remains. Rest machining computes

\[ V_{\text{rest}} = V_{\text{prior-stock}} \;\setminus\; V_{\text{target}} \;\ominus\; (\text{reach of prior tool}), \]

then restricts the new path to \(V_{\text{rest}}\). Equivalently, any location where the previous tool of radius \(R_1\) left a fillet larger than the design corner, or where its diameter could not enter a slot narrower than \(2R_1\), becomes a rest region for a tool of radius \(R_2 < R_1\). The classic case is a concave corner of design radius \(\rho\): a roughing tool with \(R_1 > \rho\) leaves an uncut wedge that the rest pass clears.

The payoff is eliminating **air cutting**. Without rest logic, a second, smaller tool would traverse the entire part at slow feeds even though most of it is already at size, wasting cycle time and wearing the tool needlessly. By touching only the leftover material, rest machining lets a size-descending sequence of tools each work only where it is needed, which is the standard way molds, dies, and deep-cornered parts are roughed to near-net shape before finishing.

## Accuracy and dependencies

Rest machining is only as trustworthy as its stock model. A coarse voxel or z-map resolution can either leave slivers of stock (gouging the finish tool later) or falsely report material as removed, so the discretization must be finer than the smallest feature and the tightest tolerance. It is the shared substrate for several other strategies: **adaptive clearing** tracks the same evolving stock boundary to hold constant engagement, and **pencil/corner finishing** is essentially rest finishing specialized to internal fillets. Chaining operations with a persistent IPW is what makes an entire multi-tool roughing plan efficient and predictable.
