**Constructive Solid Geometry (CSG)** represents a solid as an algebraic expression: simple **primitive** solids (block, cylinder, sphere, cone, torus, half-space) are combined with **regularized Boolean set operations** and rigid **transformations**. The natural data structure is a **binary tree** whose leaves are transformed primitives and whose internal nodes are operators. The tree is a *procedure* for building the solid, not the solid's boundary itself, which makes it compact, always valid, and trivially editable: change a leaf's radius or an operator, and the solid updates.

<svg viewBox="0 0 260 150" width="260" height="150" stroke="currentColor" fill="none" stroke-width="1.5">
  <circle cx="130" cy="25" r="14"/>
  <text x="122" y="29" font-size="11" stroke="none" fill="currentColor">-</text>
  <line x1="120" y1="36" x2="75" y2="64"/>
  <line x1="140" y1="36" x2="185" y2="64"/>
  <circle cx="70" cy="78" r="14"/>
  <text x="64" y="82" font-size="11" stroke="none" fill="currentColor">U</text>
  <text x="178" y="82" font-size="11" stroke="none" fill="currentColor">cyl</text>
  <line x1="60" y1="89" x2="35" y2="120"/>
  <line x1="80" y1="89" x2="105" y2="120"/>
  <text x="22" y="135" font-size="11" stroke="none" fill="currentColor">block</text>
  <text x="95" y="135" font-size="11" stroke="none" fill="currentColor">sphere</text>
</svg>

The operators are the **regularized** union, intersection, and difference, written \( \cup^{*}, \cap^{*}, -^{*} \). Ordinary set operations on solids can create geometrically meaningless artifacts: subtracting two touching blocks might leave a zero-thickness membrane or a dangling face. Regularization removes these lower-dimensional bits by taking the closure of the interior of the naive result,

\[ A \;\text{op}^{*}\; B \;=\; \operatorname{cl}\big(\operatorname{int}(A \,\text{op}\, B)\big), \]

which guarantees the outcome is again a **regular set** (a solid equal to the closure of its own interior). Because the class of regular solids is closed under regularized Booleans, a CSG tree is *always* a valid solid, no matter how it is edited. This closure property is CSG's signature strength and stands in contrast to a hand-built B-rep, which can be driven into invalid states.

CSG is naturally **unevaluated**: the tree stores the recipe, and questions are answered by recursion. The core query is **point membership classification (PMC)**: to decide whether a point is in, on, or out of the solid, classify it against each leaf primitive (easy, since primitives have analytic inside tests) and combine the answers up the tree per the Boolean operators. Rendering by ray casting works the same way, classifying ray intervals against primitives and merging them; a boundary or mesh is produced only when explicitly *evaluated*, for example by boundary evaluation (b-rep conversion) or by sampling. Mass properties such as volume and centroid can also be integrated directly over the tree.

Historically CSG and B-rep were competing paradigms; modern systems are **hybrid**. The user-visible **feature tree** of a contemporary parametric modeler is a direct descendant of the CSG tree (an ordered, editable procedure), while the kernel keeps an evaluated B-rep for display, precise selection, and analysis. Understanding CSG clarifies why parametric history is so powerful (compact, reusable, always reconstructible) and why boundary evaluation, the step that turns the recipe into an explicit skin, is where robustness engineering actually happens.
