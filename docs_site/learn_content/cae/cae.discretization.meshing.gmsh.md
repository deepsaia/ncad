**Gmsh** is an open-source three-dimensional finite element mesh generator that bundles a geometry engine, meshing algorithms, and post-processing in a single scriptable tool. It exists because turning a CAD solid into a solver-ready mesh is a discrete, error-prone pipeline stage, and a reproducible, automatable mesher is what lets an analysis be regenerated deterministically from its geometry. Gmsh is organized around four modules, applied in order: **geometry**, **mesh**, **solver**, and **post-processing**.

## The meshing pipeline

Geometry is defined either through Gmsh's own boundary-representation kernel or through an embedded OpenCASCADE kernel that can import standard CAD exchange formats (for example STEP and IGES) and perform boolean operations. The model is described hierarchically as a **boundary representation**: points bound curves, curves bound surfaces, and surfaces bound volumes. Meshing then proceeds dimension by dimension, respecting that hierarchy: 1D curves are discretized first, then 2D surfaces, then 3D volumes. This ordering guarantees that shared entities are meshed conformally, so adjacent surfaces and volumes agree on their common edges and faces.

Each dimension offers a choice of algorithm. For surfaces these include Delaunay, frontal-Delaunay, and other advancing-front and packing methods; for volumes, Delaunay and frontal tetrahedral algorithms, with recombination options to produce quadrilateral or hexahedral-dominant meshes where possible. Element size is controlled by a **mesh size field**, a scalar function \(h(\mathbf{x})\) that can be prescribed per point, derived from geometric curvature, or driven by distance from a feature, so the mesh can be refined locally where resolution is needed and coarsened elsewhere:

\[ h(\mathbf{x}) = \min\big(h_{\text{curv}}(\mathbf{x}),\; h_{\text{dist}}(\mathbf{x}),\; h_{\text{user}}(\mathbf{x})\big). \]

## Physical groups and interoperability

A feature central to using Gmsh as an export front-end is the **physical group**: a named tag that collects geometric entities (a set of surfaces, a volume) into a labeled region. Physical groups are how boundary conditions and material regions survive the trip from geometry to solver, because the mesh writes out the tags rather than raw entity numbers. Loads, supports, and material assignments in the downstream analysis reference these names, so an export deck stays meaningful even as the underlying mesh is regenerated.

Gmsh reads and writes its native **MSH** format (which carries nodes, elements, and physical tags) and interoperates with many other mesh and CAD formats. Everything the graphical interface can do is also expressible through the `.geo` scripting language and a programmable API, which makes the whole geometry-to-mesh process reproducible and parameter-driven, exactly the property an automated export pipeline requires: the same input geometry and size fields yield the same mesh every time.
