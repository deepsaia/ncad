**STEP** (ISO 10303, STandard for the Exchange of Product model data) is the dominant neutral
format for exchanging exact B-rep solids between CAD systems. Where a native file is
vendor-locked, STEP carries the precise geometry (surfaces, curves, topology) in an open,
standardized schema that any conforming system can read and write.

## Application protocols

STEP is organized into **application protocols** (APs):

- **AP203** and **AP214**: exchange of exact solid geometry and assemblies, AP214 adds colors,
  materials, and mechanical-design context. These are the workhorses for part and assembly
  interchange.
- **AP242**: the modern convergence of 203/214, adding **PMI** (product manufacturing information,
  tolerances, annotations) and richer assembly structure, the target for a fully model-based
  definition.

## Exact, not approximate

STEP preserves the **B-rep**: a cylinder round-trips as a cylindrical surface, not a faceted
approximation, which is what makes it suitable for downstream machining and analysis (unlike a mesh
format). A modeling engine writes STEP via the kernel's exchange layer (OpenCASCADE's XCAF/XDE for
AP242 with PMI and assembly structure) and reads it back for the import-and-edit workflow. STEP is
the interoperability floor for mechanical CAD: the format you export to hand a part to a supplier, a
machinist, or another CAD tool without loss of exact geometry.
