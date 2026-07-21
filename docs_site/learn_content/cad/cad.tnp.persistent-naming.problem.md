Feature-based parametric modeling represents a solid not as a static shape but as an ordered program: a base feature followed by a sequence of operations (extrude, cut, fillet, shell, pattern, sketch-on-face) that each consume the result of the previous step. Almost every operation must *point at* geometry produced earlier: "chamfer this edge," "start a sketch on that face," "use this face as the draft neutral plane." Those pointers are stored in the feature tree and must survive editing. When a parameter changes and the model is re-evaluated, the boundary representation (B-rep) is rebuilt from scratch, and each stored reference has to rebind to the topological entity the designer originally meant. The **topological naming problem** (also called the **persistent naming problem**) is the problem of assigning names to faces, edges, and vertices that remain valid across these rebuilds, so that downstream features stay attached to the right geometry.

The difficulty is that a B-rep kernel has no intrinsic, durable identity for topological entities. Faces and edges are created fresh on each evaluation and are typically identified only by their position in an internal list or by transient pointers. Two things break naive schemes. First, an upstream edit renumbers or reorders entities, so an index-based reference such as "edge 7" silently rebinds to a different edge. Second, and more fundamentally, operations do not preserve a clean one-to-one correspondence between the topology before and after an edit: a cut *splits* one face into two, a fillet *merges* or *consumes* an edge, a Boolean *creates* new seam edges and *destroys* others. Every entity therefore carries a genealogy of birth, split, merge, and death events, and even a conceptually stable reference may have no unique successor after a change.

## Naming versus matching

Formal treatments split the problem into two sub-problems. *Name generation* records, at creation time, a durable descriptor for each entity; *name matching* (identification) locates, in a freshly rebuilt model, the entity that corresponds to a stored name. A robust descriptor cannot rely on geometry, because coordinates and surface equations move whenever a dimension changes, nor on evaluation order, because reordering is exactly what edits cause. Instead, entities are named by their **generative history and topological context**: which feature created them, and which other named entities bound or adjoin them. An edge, being lower-dimensional, is commonly named by the ordered pair of faces it separates; a vertex by the edges or faces meeting at it. This is the essence of the mechanism proposed in the seminal work on the subject, which names each entity by the operation that generated it plus a topological neighborhood used to disambiguate, together with a matching algorithm that resolves the ambiguous cases.

Seen abstractly, identification is a constrained graph-matching problem over the B-rep adjacency graph \( G = (V, E) \), whose nodes are topological entities and whose arcs are incidence relations. We seek a correspondence

\[ \phi : \mathcal{T}_{\text{old}} \rightharpoonup \mathcal{T}_{\text{new}} \]

between the pre-edit and post-edit entities that is consistent with the recorded names and adjacencies. When an edit leaves the local topology unchanged, \( \phi \) is a partial isomorphism and matching is exact. When the topology changes, \( \phi \) becomes a one-to-many or many-to-one relation (a split maps one parent to several children; a merge maps several parents to one child), and identification degrades into an *approximate* match guided by ancestry and by which neighboring named entities survived. Disambiguation of a split then reduces to comparing the candidate children against the recorded neighborhood, for example choosing the child that still borders the same named companion face.

## Where it bites, and why it is hard to eliminate

The consequences are what designers experience as *rebuild errors*, *feature failures*, or "sick" features: change an early dimension and a downstream fillet suddenly fails, jumps to the wrong edge, or drops entirely. The diagram below shows the canonical trap. A face \(F\) is chosen as a reference; an unrelated upstream edit later cuts that face in two, and the stored name for \(F\) must now resolve to \(F_1\), \(F_2\), both, or neither, with no purely local rule that is always right.

<svg viewBox="0 0 420 150" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1.5">
  <defs>
    <marker id="arrow" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0 0 L6 3 L0 6"/>
    </marker>
  </defs>
  <rect x="20" y="40" width="120" height="80"/>
  <text x="72" y="85" fill="currentColor" stroke="none" font-size="13">F</text>
  <text x="20" y="28" fill="currentColor" stroke="none" font-size="11">reference stored on F</text>
  <path d="M158 80 h44" marker-end="url(#arrow)"/>
  <text x="170" y="70" fill="currentColor" stroke="none" font-size="10">edit</text>
  <rect x="240" y="40" width="120" height="80"/>
  <line x1="300" y1="40" x2="300" y2="120"/>
  <text x="262" y="85" fill="currentColor" stroke="none" font-size="13">F1</text>
  <text x="322" y="85" fill="currentColor" stroke="none" font-size="13">F2</text>
  <text x="240" y="28" fill="currentColor" stroke="none" font-size="11">upstream cut splits F</text>
</svg>

Practical schemes therefore log split and merge events explicitly, propagate a parent's name to its children with a distinguishing suffix, and fall back to neighborhood matching when exact invariance fails; deterministic re-evaluation (same specification producing the same topology in the same order) further contains the problem by ensuring nothing changes unless an edit forces it. Because a fully general solution is provably out of reach (there is no coordinate-free rule that unambiguously tracks every entity through arbitrary topology changes), robustness is measured by how gracefully a system handles the ambiguous cases rather than by a promise to eliminate them. This is also why some workflows adopt *history-free* (direct) modeling, which keeps no replayable feature tree and thus has no persistent references to break, at the cost of losing parametric editability; hybrid modelers try to keep both, and inevitably confront the naming problem again at the boundary between the associative and explicit representations.
