Topology alone records connectivity but says nothing about *where things are* in space. A B-rep becomes a concrete solid only when each topological entity is bound to a **geometric carrier**: a vertex carries a **point**, an edge carries a **curve**, and a face carries a **surface**. This clean separation is deliberate. It lets the same connectivity describe infinitely many differently shaped solids, isolates all floating-point error into the geometry layer, and allows topology-preserving edits (like moving a hole) to change geometry without re-deriving the graph.

The carriers are almost always **parametric**. A surface is a map \( \mathbf{S}(u,v):\Omega\subset\mathbb{R}^2 \to \mathbb{R}^3 \) and a curve is a map \( \mathbf{C}(t):[a,b]\to\mathbb{R}^3 \), typically expressed as NURBS, analytic primitives (plane, cylinder, cone, sphere, torus), or procedurally swept/blended surfaces. Crucially, a face's underlying surface is usually *larger* than the face itself: the face is the sub-region of that surface **trimmed** by its loops. Trimming is often stored twice for robustness, as 3D edge curves and as 2D **parameter-space curves (p-curves)** living in the surface's \((u,v)\) domain, so that the same edge can be evaluated either in model space or directly in the domain of each adjacent face.

<svg viewBox="0 0 240 140" width="240" height="140" stroke="currentColor" fill="none" stroke-width="1.5">
  <rect x="20" y="20" width="90" height="90"/>
  <text x="20" y="128" font-size="10" stroke="none" fill="currentColor">(u,v) domain</text>
  <path d="M35,40 C55,30 75,55 90,45"/>
  <path d="M35,40 C45,70 70,80 90,45" stroke-dasharray="3 3"/>
  <path d="M150,25 C175,20 210,45 210,70 C210,100 175,115 150,110 C160,80 160,55 150,25 Z"/>
  <text x="150" y="128" font-size="10" stroke="none" fill="currentColor">trimmed face in 3D</text>
  <line x1="115" y1="65" x2="145" y2="65" stroke-dasharray="2 2"/>
  <text x="116" y="58" font-size="9" stroke="none" fill="currentColor">S(u,v)</text>
</svg>

Because topology and geometry are stored redundantly, they must be kept mutually **consistent within a tolerance**. An edge's curve is shared by two faces, yet in general the intersection of two independently defined NURBS surfaces has no exact rational parameterization, so the stored edge curve only *approximately* lies on both surfaces. Professional kernels therefore attach a **tolerance** to each vertex and edge (tolerant modeling): the geometry is guaranteed to lie within that radius of the ideal, and downstream operations must respect it. Vertices must lie on their incident edge curves, edge endpoints must coincide with vertex points, and every point of an edge must lie on both adjacent surfaces, all to within model tolerance. Violations of these gap and coincidence conditions are the usual cause of "invalid B-rep" errors.

This attachment layer is exactly what ratified exchange standards formalize so that a solid can move between systems without loss: geometric entities (points, curves, surfaces) and topological entities (vertices, edges, faces, shells) are defined as distinct schemas that reference one another. When designing or debugging a modeler, it pays to treat the two layers with different mindsets: topology should be reasoned about combinatorially and kept exact, while geometry is numerical, tolerant, and the place where robustness engineering (intersection, projection, healing) is concentrated.
