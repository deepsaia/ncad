A master CAD model is large, proprietary, and precise, more than most consumers of it actually need. Manufacturing planners, design reviewers, procurement, and technical-documentation teams mostly need to *see* the geometry, read its PMI, and navigate the assembly, without a CAD license and without the right (or the compute budget) to edit it. **Lightweight viewables** answer that need: compact, derived representations optimized for visualization, markup, and long-term reference. The two most important are **JT** and **3D PDF**, and they anchor the digital-mockup (DMU) and model-based-definition publishing workflows that let a design be consumed across a whole supply chain.

## JT (ISO 14306)

JT is a segment-structured format organized around a **logical scene graph** (the assembly/part hierarchy with transforms), plus one or more **tessellated mesh** segments carrying multiple *levels of detail* (LODs), and optional segments for precise geometry (a kernel B-rep segment, with a STEP-based B-rep added in the second edition), PMI, metadata, and textures. It is aggressively compressed, topologically compact meshes and quantized coordinates, and supports partial/streamed loading, so a multi-thousand-part assembly can be opened and spun interactively while only the visible, appropriately-detailed pieces are resident. Because it can hold *both* fast tessellation and, when needed, exact B-rep, JT spans the range from pure viewable to near-authoring reference, which is why it was standardized as ISO 14306 for neutral, royalty-free adoption.

## 3D PDF

3D PDF reuses the ubiquitous PDF container (ISO 32000) and embeds an interactive 3D annotation. The 3D payload is one of two standardized streams: **U3D** (Universal 3D, ECMA-363), which is tessellation-oriented, or **PRC** (Product Representation Compact, ISO 14739), which is more compact and can carry both tessellation and optional exact B-rep. On top of the geometry it layers a model tree, named views, and PMI. Its decisive advantage is *reach*: the recipient opens the file in a reader they already have, no CAD, no viewer install, which makes 3D PDF ideal for approvals, work instructions, and distributing MBD data to parties outside the engineering toolchain.

## The governing idea: bounded tessellation

Both formats lean on approximating smooth surfaces with triangle meshes to a controlled tolerance. The key metric is **chordal deviation**, the maximum gap \(\epsilon\) between a curved surface and its facet. For a surface patch of local radius of curvature \(r\) spanned by a facet subtending angle \(\theta\), the sagitta (chord height error) is

\[ \epsilon = r\left(1-\cos\tfrac{\theta}{2}\right)\approx \frac{r\,\theta^{2}}{8}, \]

so halving the allowed deviation roughly quadruples the facet count, tighter tolerance means smoother appearance at the cost of file size and draw time. LOD hierarchies exploit this directly by storing several discretizations of the same shape and swapping in a coarser one when the object is small on screen or far from the camera. The design tension across every viewable, fidelity versus footprint, is exactly this tradeoff made explicit, which is why lightweight formats are deliberately *lossy derivatives* rather than replacements for the authoritative master model.
