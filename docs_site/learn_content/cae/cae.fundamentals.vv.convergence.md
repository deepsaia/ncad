A finite-element result is an *approximation* of the continuum solution, and its error shrinks only as the discretization is refined. Trusting a single mesh is one of the most common mistakes in engineering simulation. **Mesh convergence** and the broader discipline of **verification and validation (V&V)** are the practices that turn a colorful stress plot into a defensible engineering claim.

## Discretization error and convergence

For a well-posed elliptic problem solved with elements of polynomial order \( p \), the error in an integral quantity decreases with the characteristic element size \( h \) at an asymptotic rate

\[ \lVert u - u_h \rVert \;\le\; C\, h^{\,q}, \]

where \( q \) depends on the element order and the smoothness of the solution. Refinement therefore comes in two flavors: **h-refinement** (smaller elements) and **p-refinement** (higher-order shape functions). A convergence study runs the same model on a sequence of meshes and tracks a target quantity (peak stress, tip deflection, natural frequency) until successive changes fall below a tolerance. Because coarse-mesh error is often non-conservative, the change between refinements, not the absolute value on one mesh, is the evidence. **Richardson extrapolation** estimates the mesh-independent value from two or three grids with refinement ratio \( r \),

\[ f_{h\to 0} \approx f_1 + \frac{f_1 - f_2}{r^{\,p} - 1}, \]

and the **Grid Convergence Index** wraps that estimate in a safety factor to report a discretization uncertainty band. A crucial caveat: at a geometric singularity (a sharp re-entrant corner, a point load), the true stress is infinite and the solution *will not converge*. Such hot spots must be de-featured, filleted, or assessed with a criterion that does not depend on the singular peak.

## Verification versus validation

The two words are precise and not interchangeable. **Verification** asks "are we solving the equations right?" It is a mathematics question about the code and the mesh, split into *code verification* (comparing against exact or manufactured solutions to confirm the implemented order of accuracy) and *solution verification* (estimating the discretization error of a specific run, as above). **Validation** asks "are we solving the right equations?" It is a physics question, answered by comparing simulation output against physical experiment with quantified uncertainty on both sides. A model can be perfectly verified yet invalid (right math, wrong physics), or physically sound yet unverified (right model, under-resolved mesh).

## Why it matters

This hierarchy, formalized by consensus standards, is what lets simulation substitute for or complement testing in regulated and safety-critical work. It also clarifies responsibilities in a modeling workflow: convergence and solution verification are properties the analyst controls through mesh and element choices in the owned model, while code verification is a property of the delegated solver. Treating convergence studies and V&V as regression nets, run automatically as the model or solver changes, keeps results reproducible rather than anecdotal.
