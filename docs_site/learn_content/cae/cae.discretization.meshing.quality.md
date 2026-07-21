Once the element families are chosen, two further decisions shape a mesh: whether it is **structured** or **unstructured**, and how good the individual elements are. Both directly affect solution accuracy, solver conditioning, and whether the analysis converges at all.

## Structured versus unstructured

A **structured** mesh has implicit connectivity: its cells are addressed by a regular index tuple \((i,j,k)\), so each interior node's neighbors are known by arithmetic rather than stored in a table. It is built from quadrilaterals (2D) or hexahedra (3D) laid out in logically rectangular blocks. This regularity gives compact storage, banded matrices, easy high-order stencils, and excellent control over boundary-layer resolution, which is why it is favored in high-fidelity fluid dynamics. Its drawback is geometric: fitting a structured grid to a complex part is labor-intensive, often requiring the domain to be hand-decomposed into a **block-structured** or **multi-block** assembly. An **unstructured** mesh stores explicit connectivity (an element-to-node table) and may mix element types freely, so tetrahedral (and hybrid) meshers can fill arbitrarily complex geometry almost automatically. The price is higher memory per cell, irregular sparse matrices, and generally more elements to reach the same accuracy. Most general-purpose analysis today is unstructured or hybrid; structured meshing is reserved where its accuracy and efficiency justify the manual effort.

## Why quality matters

Regardless of type, individual element **quality** controls the error and the conditioning of the discrete system. A well-shaped element is close to its ideal (equilateral or right-angled) form; a degenerate one is stretched, flattened, or twisted. Poor elements corrupt the isoparametric mapping, inflate the discretization error, and worsen the condition number of the stiffness matrix, which slows or breaks iterative solvers and can make results locally meaningless. The classic result is that interpolation error is bounded by a factor that blows up as the maximum element angle approaches \(180^\circ\), so a single sliver element can dominate the global error.

## Common quality metrics

Meshers report several dimensionless measures, each targeting a different defect:

- **Aspect ratio**: the ratio of longest to shortest characteristic length; ideal is near \(1\), high values indicate stretched slivers.
- **Skewness**: how far a cell's angles deviate from the ideal, often \( \text{skew} = \dfrac{\theta_{\max} - \theta_{e}}{180^\circ - \theta_{e}} \) where \(\theta_e\) is the ideal angle; \(0\) is perfect, values near \(1\) are degenerate.
- **Scaled Jacobian**: the minimum of the mapping Jacobian determinant normalized over the element, measuring distortion and detecting inversion when it goes non-positive.
- **Orthogonality / non-orthogonality**: the angle between the face-normal and the vector joining adjacent cell centers, critical for finite-volume flux accuracy.
- **Warpage**: out-of-plane twist of a quadrilateral face.

For the mapping to be valid at every integration point, the Jacobian determinant must remain strictly positive,

\[ J = \det\!\left(\frac{\partial \mathbf{x}}{\partial \boldsymbol{\xi}}\right) > 0, \]

and meshing workflows typically enforce minimum thresholds on these metrics, then improve failing regions by **smoothing** (relocating nodes, e.g. Laplacian or optimization-based) and **local refinement or swapping** before the mesh is handed to the solver.
