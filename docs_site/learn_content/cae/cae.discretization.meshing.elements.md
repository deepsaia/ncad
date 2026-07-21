An element is defined by two independent choices: its **geometric family** (the shape and number of corners) and its **interpolation order** (the polynomial degree of its shape functions, set by how many nodes it carries). These choices govern how accurately a mesh represents both the geometry and the solution field, and they trade directly against the cost of generating and solving the model.

## Geometric families

Three families cover almost all 3D solid meshing. **Simplices** are the tetrahedron in 3D (triangle in 2D): they can fill any shape, so automatic meshers can tetrahedralize arbitrarily complex CAD with little user effort. **Tensor-product** elements are the hexahedron (quadrilateral in 2D): a mapped brick that aligns with structured, layered geometry and generally delivers more accuracy per degree of freedom, especially in bending, but is far harder to generate on complicated topology. **Transition** elements, the **wedge (prism)** and **pyramid**, bridge the two: prisms are ideal for extruded or boundary-layer regions (a triangle swept through the thickness), while pyramids provide the geometric glue that lets a hex region connect to a tet region across a quadrilateral face. A single unstructured mesh is often a hybrid of all of these.

## Order: linear versus quadratic

*Linear* (first-order) elements use only corner nodes and interpolate the field with linear shape functions, so their edges stay straight and their strain/flux field is constant (linear tet, TET4) or bilinear (hex, HEX8) within the element. *Quadratic* (second-order) elements add mid-edge nodes, raising the interpolation to quadratic. This has two consequences: edges can **curve** to follow real geometry, and the strain field varies linearly inside the element, which captures bending and stress gradients far better. Node counts follow directly, for example:

\[ \text{TET4} \to \text{TET10}, \qquad \text{HEX8} \to \text{HEX20}, \qquad \text{WEDGE6} \to \text{WEDGE15}. \]

A linear tetrahedron is notoriously stiff: its constant strain makes it lock and grossly over-predict stiffness in bending and near-incompressible problems, so it is a poor choice for stress analysis. The quadratic tetrahedron (TET10) largely removes this defect and is the workhorse for automatically meshed stress models, at the cost of more nodes per element. This is the core rule of thumb: use **quadratic** elements for accurate stress/strain fields, and reserve linear elements for contact-dominated, explicit-dynamics, or thermal models where their behavior is acceptable and their low cost matters.

## Integration and validity

Element matrices are formed by Gauss quadrature over a reference element, mapped to physical space by the isoparametric Jacobian; the number of integration points is chosen to integrate the element's polynomial order exactly (**full integration**) or one order lower (**reduced integration**). Reduced integration is cheaper and can cure locking, but it can admit spurious zero-energy *hourglass* modes that must be stabilized. For any element to be valid, the mapping Jacobian determinant must stay positive everywhere in the element,

\[ J(\xi,\eta,\zeta) = \det\!\left(\frac{\partial \mathbf{x}}{\partial(\xi,\eta,\zeta)}\right) > 0, \]

otherwise the element is inverted or badly distorted and the solution is meaningless. This constraint links element order to mesh quality: curved quadratic elements can more faithfully wrap curved geometry, but their mid-side nodes must be placed so the Jacobian never goes negative.
