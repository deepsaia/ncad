A **boundary representation (B-rep)** describes a solid not by the volume it occupies but by the closed, orientable *skin* that separates its interior from the exterior. That skin is stored as two interlocking layers: **topology**, the purely combinatorial record of *how* pieces of the boundary connect, and **geometry**, the metric shapes those pieces actually take (covered separately). Topology is what makes a B-rep robust and editable: it is a graph of adjacency that survives small numerical perturbations of the underlying geometry and gives modeling operations O(1) access to neighbors.

The topological entities form a strict containment hierarchy, from a whole body down to a single point:

- **Solid (body):** one connected chunk of material, bounded by one or more shells.
- **Shell:** a maximal connected set of faces forming a closed watertight surface. A solid has one outer shell; each internal void (a cavity fully enclosed by material) adds another shell.
- **Face:** a bounded, orientable patch of the boundary. Its extent is defined by its loops.
- **Loop:** an ordered, closed circuit of edges bounding a face. Each face has exactly one *outer* loop and zero or more *inner* loops (rings) that cut holes into it.
- **Edge:** a bounded curve segment shared between faces, terminated by two vertices.
- **Vertex:** a single 0-dimensional point where edges meet.

<svg viewBox="0 0 260 160" width="260" height="160" stroke="currentColor" fill="none" stroke-width="1.5">
  <polygon points="40,120 150,120 150,40 40,40"/>
  <polygon points="150,120 210,90 210,10 150,40"/>
  <polyline points="40,40 100,10 210,10"/>
  <polyline points="100,10 100,90 40,120" stroke-dasharray="3 3"/>
  <polyline points="100,90 210,90" stroke-dasharray="3 3"/>
  <circle cx="40" cy="120" r="3"/>
  <text x="18" y="135" font-size="11" stroke="none" fill="currentColor">vertex</text>
  <text x="92" y="85" font-size="11" stroke="none" fill="currentColor">edge</text>
  <text x="78" y="90" font-size="11" stroke="none" fill="currentColor">face</text>
</svg>

Orientation is a first-class part of the topology, not an afterthought. Face normals are conventionally directed *away* from the solid material, and each loop is traversed so that the material lies consistently on one side (for example, outer loops counterclockwise and inner loops clockwise when viewed from outside). This orientation is what lets an algorithm decide inside from outside. The central well-formedness rule for a two-manifold solid is that **every edge is shared by exactly two faces**; a manifold vertex has a single fan of faces cycling around it. Edges shared by one face (a boundary sheet) or by more than two faces (a non-manifold junction) violate the manifold condition and require an extended data model.

Because modeling operations constantly ask questions like "which faces meet at this edge" or "walk the edges around this vertex," the adjacency is stored explicitly in structures such as the **winged-edge**, **half-edge (doubly-connected edge list)**, or the non-manifold **radial-edge**. In a half-edge model each edge is split into two oppositely oriented half-edges, one per adjacent face, each carrying pointers to its origin vertex, its face, and the next half-edge in the loop, so any local neighborhood can be traversed in constant time. The correctness of any such structure is checkable against the **Euler-Poincaré relation** \( V - E + F - R = 2(S - G) \), where \(V,E,F\) count vertices, edges, faces, \(R\) counts inner loops (rings), \(S\) counts shells, and \(G\) is the genus (through-holes). A final, practical concern is **persistent identity**: because downstream references (dimensions, features, mates) point at faces and edges by name, professional kernels assign stable identifiers that survive rebuilds, rather than relying on positional order that shifts as the model changes.
