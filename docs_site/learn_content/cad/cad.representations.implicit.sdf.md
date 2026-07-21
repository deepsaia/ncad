An **implicit** representation defines a solid not by its boundary but by a scalar field \( f:\mathbb{R}^3 \to \mathbb{R} \) whose sign encodes inside versus outside. The surface is the **zero level set** \( \{\mathbf{x} : f(\mathbf{x}) = 0\} \). A **signed distance function (SDF)** is the special, information-rich case where the magnitude of \(f\) equals the Euclidean distance to the boundary:

\[ f(\mathbf{x}) = \pm \min_{\mathbf{y}\in\partial\Omega} \lVert \mathbf{x} - \mathbf{y}\rVert, \]

with the sign taken negative inside the solid and positive outside (conventions vary). By construction an SDF satisfies the **Eikonal equation** \( \lVert \nabla f \rVert = 1 \) almost everywhere, and where it is differentiable the gradient is the outward unit **surface normal**, \( \mathbf{n} = \nabla f \). So a single field supplies not only membership but distance and orientation for free.

The defining convenience of SDFs is that constructive operations become simple algebra on field values. Regularized Booleans reduce to min and max,

\[ f_{A\cup B} = \min(f_A, f_B), \quad f_{A\cap B} = \max(f_A, f_B), \quad f_{A - B} = \max(f_A, -f_B), \]

a constant **offset** (shelling, clearance, tolerance) is just \( f(\mathbf{x}) - r \), and **smooth blends** (fillet-like transitions) come from soft-min variants that round the seam. These closed-form combinations always yield another well-defined field, so the result is guaranteed closed and non-self-intersecting, and complex **lattices**, gyroids, and graded infill are expressed as compact periodic functions rather than millions of explicit faces.

Storage and evaluation take two forms. An **analytic** SDF is a small procedure (composed primitives and operators) evaluated on demand, exact and resolution-independent; a **sampled** SDF stores field values on a grid or, more efficiently, an **adaptive octree / narrow band** around the surface, trading exactness for a bounded, queryable representation. Rendering typically uses **sphere tracing**: because \(f\) is a distance bound, a ray at point \(\mathbf{x}\) can safely advance by \(f(\mathbf{x})\) without crossing the surface, so the march

\[ t_{k+1} = t_k + f(\mathbf{r}(t_k)) \]

converges to the first intersection. An explicit mesh is extracted when needed via isosurfacing such as marching cubes or dual contouring.

SDFs shine where booleans, offsets, blends, and volumetric infill dominate, and where guaranteed-watertight output matters (additive manufacturing, implicit lattice design, level-set simulation). Their limitations are the mirror image of B-rep's strengths: **sharp features** (crisp edges, exact fillets) are hard to reproduce on a sampled grid without special dual methods; the surface has no persistent named faces or edges to dimension or reference; and dense grids are memory-hungry, which is why adaptive and narrow-band schemes exist. In practice implicit and boundary representations are complementary, and mature pipelines convert between them as the operation demands.
