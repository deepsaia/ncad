Curvature analysis quantifies how sharply a curve or surface bends, and it is the most direct numeric handle on shape quality, manufacturability, and continuity. For a parametric curve \(\mathbf{r}(t)\) the (unsigned) curvature is

\[
\kappa = \frac{\lVert \mathbf{r}'\times\mathbf{r}'' \rVert}{\lVert \mathbf{r}' \rVert^{3}},
\]

the reciprocal of the local radius of the osculating circle. A curvature comb visualizes this by drawing, at samples along the curve, a needle normal to the curve whose length is proportional to \(\kappa\); connecting the needle tips gives the comb back. The comb makes defects obvious to the eye: flat spots appear as short needles, inflection points appear where needles flip to the opposite side (a sign change in signed curvature), and continuity breaks appear as jumps or kinks in the comb back.

<svg viewBox="0 0 240 110" width="240" height="110" stroke="currentColor" fill="none" stroke-width="1.4"><path d="M20,80 C70,30 170,30 220,80"/><line x1="20" y1="80" x2="20" y2="72"/><line x1="60" y1="48" x2="60" y2="28"/><line x1="120" y1="38" x2="120" y2="8"/><line x1="180" y1="48" x2="180" y2="28"/><line x1="220" y1="80" x2="220" y2="72"/><polyline points="20,72 60,28 120,8 180,28 220,72" stroke-dasharray="3 3"/></svg>

## Surface curvature

On a surface the bending depends on direction. At a point, the normal curvature varies as the cutting plane rotates, and its two extrema are the principal curvatures \(\kappa_1,\kappa_2\), attained along orthogonal principal directions. They follow from the first fundamental form coefficients \(E,F,G\) (the intrinsic metric) and the second fundamental form coefficients \(L,M,N\) (how the normal turns). The two scalar invariants used in practice are Gaussian curvature and mean curvature:

\[
K = \kappa_1\kappa_2 = \frac{LN - M^2}{EG - F^2},\qquad H = \tfrac{1}{2}(\kappa_1+\kappa_2) = \frac{EN - 2FM + GL}{2\,(EG - F^2)}.
\]

The principal curvatures are recovered as the roots of \(\kappa^2 - 2H\kappa + K = 0\), giving \(\kappa = H \pm \sqrt{H^2 - K}\).

The sign of \(K\) classifies the local shape: \(K>0\) is elliptic (dome or bowl, both principal curvatures same sign), \(K<0\) is hyperbolic (saddle), and \(K=0\) is parabolic or planar. Crucially, \(K\) is intrinsic (Gauss's Theorema Egregium): it is invariant under bending without stretching. That is exactly why developable surfaces, which can be unrolled flat, are characterized by \(K\equiv 0\), a property directly exploited in sheet-metal unfolding and composite ply layup.

Curvature maps and combs are read-only diagnostics but they drive real decisions. A color map of \(K\) or \(H\) exposes unwanted saddles, flats, and ripples that a shaded render hides; the minimum principal radius \(1/\kappa_{\max}\) bounds the largest fillet and the largest offset or wall thickness that will not self-intersect; and near-zero \(K\) regions flag where a surface can be manufactured from flat stock. Curvature analysis is thus both a quality lens and a manufacturability gate.
