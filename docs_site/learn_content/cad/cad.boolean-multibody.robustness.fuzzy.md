Boolean operations (union, intersection, difference) on solid bodies are the workhorse of multibody modeling, and they are also the single most fragile step in a boundary-representation (B-rep) kernel. A B-rep stores geometry as trimmed surfaces, curves, and points, with topology (faces, edges, vertices) referencing that geometry. Because every surface intersection is computed in finite-precision floating point, coincidences that are exact in the design intent (two faces meeting along an edge, an edge lying on a face) are only ever *approximate* numerically. To cope, a tolerant B-rep attaches a **tolerance** to each topological entity: a vertex owns a tolerance sphere, an edge a tolerance tube, a face a tolerance band. Two entities are treated as coincident when the distance between their geometries falls inside the combined band.

## The intersection is where it breaks

A Boolean reduces to three sub-problems: intersect the faces/edges of the two operands, classify the resulting pieces as inside, outside, or on the other solid, and stitch the kept pieces into a closed, manifold shell. The intersection is the ill-conditioned part. Near-tangent surfaces, glancing edges, and nearly coincident faces produce section curves whose numerical conditioning is poor: a tolerance chosen too small will *miss* an intersection (leaving a crack in the shell), or emit spurious sub-micron edges and sliver faces, so the result fails to close or comes back non-manifold. Detection of coincidence within the operation can be written as a single distance gate against the sum of the participating tolerances plus an extra allowance \(f\):

\[ d(A, B) \;\le\; t_A + t_B + f \]

## Fuzzy value: an explicit intersection allowance

A **fuzzy Boolean** exposes that extra allowance \(f\) (the *fuzzy value*) as an explicit input, added to the natural tolerances of the operands for the duration of the operation. Inflating the band makes near-coincident geometry register as coincident, bridges gaps narrower than \(f\), and collapses micro-features below \(f\) instead of producing degenerate slivers. The governing trade-off is stark and bidirectional: too small and the operation fails or emits invalid topology; too large and genuine small features are destroyed and the result is dimensionally wrong (a real 5 micron step erased because \(f\) exceeded it). The fuzzy value is therefore never a global crank-it-up knob; it is a bounded intervention tied to the characteristic size of the model.

## Tolerance gating and the retry ladder

Robust pipelines make the choice adaptive. **Tolerance gating with fuzzy retry** runs the Boolean first at the tight default tolerance; only on failure does it escalate along a bounded ladder, commonly geometric,

\[ f_k = f_0 \, r^{\,k}, \qquad r \approx 10, \qquad f_k \le \lambda \, D_{\text{bbox}} \]

where \(D_{\text{bbox}}\) is the bounding-box diagonal and \(\lambda\) a small cap (a fraction of a percent). The word *gating* is the important half: a fuzzy result is accepted only if it passes a hard validity check (closed shell, correct orientation, no self-intersections via a section-intersection test) **and** preserves expected invariants such as the solid count and a volume that lands within a plausible band of the analytic expectation. Escalation stops at the first tolerance that both succeeds and passes the gate. This converts a brittle all-or-nothing algorithm into a controlled search, and it prevents the failure mode that quietly discredits a modeler: silently returning a geometrically wrong body because the tolerance was cranked until *something* closed.

Where it matters most is in downstream-heavy workflows. A body that closed only because of an oversized fuzzy value may still carry hidden slivers or an over-inflated vertex tolerance, and the next operation (a fillet, a shell, a section for meshing) will inherit and amplify that defect. Recording the fuzzy value that was actually used, and gating on invariants rather than on mere non-emptiness of the result, keeps the tolerance budget auditable across a long feature history.
