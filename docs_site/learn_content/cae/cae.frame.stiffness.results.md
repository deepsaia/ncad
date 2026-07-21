Solving \( \mathbf{K}\mathbf{u} = \mathbf{f} \) yields the nodal displacements, but the quantities an engineer actually designs against, **deflections, support reactions, and internal member forces**, are recovered in a distinct post-processing stage. This recovery step reverses the assembly logic of the direct stiffness method: it maps the global solution back onto each element to extract the forces flowing through it, and back onto the supports to find what the structure pushes against.

## Deflections

The primary output is the displacement vector \( \mathbf{u} \) itself: the translations and rotations at every free node. Serviceability checks compare these against limits (a common example is a span/deflection ratio such as \(L/360\) for floor members). Values *between* nodes are interpolated with the element shape functions, and for members carrying span loads the exact particular solution of the beam equation is superposed onto the interpolated nodal field so the deflected shape is accurate along the whole member, not just at its ends.

## Member end forces

For each element, the relevant slice of the global displacement vector is rotated back into the member-local frame and multiplied by the local stiffness matrix, and the member's own fixed-end forces are added back in:

\[ \mathbf{f}_\ell = \mathbf{k}_\ell\,\mathbf{T}\,\mathbf{u}_g + \mathbf{f}_\ell^{\text{FEF}}. \]

The entries of \( \mathbf{f}_\ell \) are the axial force, shear forces, torsion, and bending moments at each end of the member, expressed in local coordinates and ready for interpretation as an axial-force, shear, and bending-moment diagram. The fixed-end term \( \mathbf{f}_\ell^{\text{FEF}} \) is essential: because span loads were converted to equivalent nodal loads during assembly, they must be reintroduced here or the internal forces will be wrong even though the global solution was correct.

## Reactions and verification

Reactions at the supports come from the restrained partition of the global system. Once the free displacements \( \mathbf{u}_f \) are known,

\[ \mathbf{r}_s = \mathbf{K}_{sf}\,\mathbf{u}_f + \mathbf{K}_{ss}\,\mathbf{u}_s - \mathbf{f}_s, \]

where \( \mathbf{f}_s \) accounts for any loads applied directly at supported DOF. A sound analysis then checks global equilibrium, \( \sum \mathbf{F} = \mathbf{0} \) and \( \sum \mathbf{M} = \mathbf{0} \): the reactions must balance all applied loads, and the residual \( \mathbf{K}\mathbf{u} - \mathbf{f} \) should be near machine zero. Summing the member end forces at each joint provides an independent local equilibrium check.

These recovered quantities are the actual deliverables of frame analysis. Axial forces and moments feed strength checks such as the combined stress \( \sigma = P/A + Mc/I \) and code utilization ratios; shear forces size connections and webs; reactions size foundations and bearings; and deflections govern serviceability. Because the recovery is a deterministic linear mapping of the solved displacements, identical models produce identical results, which is what makes the outputs suitable as regression baselines and as inputs to downstream design-code verification.
