A Boolean or feature operation rarely returns topology in its simplest form. The algorithm splits faces and edges wherever the two operands intersect, keeps the classified pieces, and reassembles them, and in doing so it routinely leaves **redundant topology**: two faces that lie on one and the same underlying surface but remain separated by a seam edge, or a chain of collinear edges stitched together through unnecessary vertices. Geometrically the seam between two coplanar (or co-cylindrical) faces carries no shape information, but it does real damage: it bloats the model, it breaks stable face selection (one logical planar wall is now three faces, so a rule that picks "the top face" becomes ambiguous), and it seeds later failures because an operation like a fillet applied across a phantom seam behaves very differently from one applied to a single continuous face.

## Unify-same-domain

**Unify-same-domain** is the post-process that removes this redundancy. It detects adjacent faces that share the same host surface (and adjacent edges that share the same host curve) within tolerance and merges them, deleting the intervening edge or vertex and re-parameterizing the merged face on the common surface. The merge criterion is geometric identity of the hosts *plus* continuity across the seam. For two faces \(F_1, F_2\) meeting along edge \(E\), with host surfaces \(S_1, S_2\), the surfaces are the same domain when a reparameterization \(\phi\) makes them coincide within tolerance,

\[ \bigl\lVert S_1(u,v) - S_2\!\bigl(\phi(u,v)\bigr) \bigr\rVert \le \varepsilon \quad \forall (u,v)\in\Omega, \]

and the surface normals agree across \(E\) (at least tangent-plane, \(C^1\), continuity). That continuity test is what stops the merge from erasing a genuine crease: two planes that meet at an angle share no domain, whereas two coplanar patches do. In practice, for analytic surfaces the test reduces to comparing surface type and defining parameters (plane through the same point with the same normal, cylinder with the same axis and radius), which is cheap and exact enough to be safe.

## Heal-and-retry

**Heal-and-retry** is the broader robustness loop that wraps the operation itself. When a Boolean or an import fails validation, blindly retrying is pointless; the input must first be normalized into a state the algorithm can digest. Shape healing is a battery of local repairs: *sewing* merges edges and vertices that are coincident within tolerance so an open shell becomes closed; degenerate and sub-tolerance edges and sliver faces are removed; wire ordering and edge orientation are fixed so face boundaries are consistent; and individual entity tolerances are selectively upgraded to bridge cracks left by data exchange or an earlier imprecise operation. The pipeline is explicit:

<svg viewBox="0 0 460 70" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1.4">
  <rect x="6"   y="22" width="70" height="26" rx="4"/>
  <text x="41"  y="39" fill="currentColor" stroke="none" font-size="11" text-anchor="middle">operate</text>
  <rect x="104" y="22" width="70" height="26" rx="4"/>
  <text x="139" y="39" fill="currentColor" stroke="none" font-size="11" text-anchor="middle">validate</text>
  <rect x="202" y="22" width="56" height="26" rx="4"/>
  <text x="230" y="39" fill="currentColor" stroke="none" font-size="11" text-anchor="middle">heal</text>
  <rect x="286" y="22" width="56" height="26" rx="4"/>
  <text x="314" y="39" fill="currentColor" stroke="none" font-size="11" text-anchor="middle">retry</text>
  <rect x="370" y="22" width="70" height="26" rx="4"/>
  <text x="405" y="39" fill="currentColor" stroke="none" font-size="11" text-anchor="middle">unify</text>
  <path d="M76 35 h28 M174 35 h28 M258 35 h28 M342 35 h28" marker-end="url(#ah)"/>
  <path d="M314 22 C314 6, 139 6, 139 22" stroke-dasharray="3 3"/>
  <text x="226" y="11" fill="currentColor" stroke="none" font-size="9" text-anchor="middle">re-validate</text>
  <defs><marker id="ah" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" stroke="currentColor"/></marker></defs>
</svg>

operate, validate, and on failure heal the operand and retry, then unify the successful result to shed the seams the operation introduced. The retry is bounded (a small number of heal passes with escalating aggressiveness) and, as with fuzzy gating, each retried result is re-validated so healing can never launder an invalid body into an accepted one.

## Ordering and where it matters

Sequence is load-bearing. Unify runs *after* a successful operation, because merging faces first would destroy the very edges the next Boolean needs to intersect against; healing runs *before* the retry, because it exists to make a rejected operand admissible. This mirrors a broader modeling truth: a B-rep kernel is order-sensitive, and a repair applied at the wrong point can turn a recoverable failure into an unrecoverable one. The payoff of doing it well is compounding. Clean, unified topology keeps face and edge identities stable across a long feature tree, keeps model size proportional to real geometric complexity rather than to Boolean history, and gives every downstream consumer (fillets, shells, draft, meshing, and data export) a body that says exactly what it means and no more.
