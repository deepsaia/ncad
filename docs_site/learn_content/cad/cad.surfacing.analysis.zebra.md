Zebra striping, isophotes, and deviation maps are read-only interrogation overlays: they change nothing about the geometry but translate its higher-order behavior into a visual pattern the eye can judge instantly. They exist because continuity defects that are invisible in a shaded view (a curvature jump, a slight normal kink) become glaring once light is mapped onto the surface, which is precisely how such defects reveal themselves on a physical painted or reflective part.

## Zebra stripes

Zebra analysis renders the surface as if it reflected a striped environment of alternating light and dark bands, so the stripe pattern behaves like reflected straight lines. The way stripes meet across a shared edge diagnoses the continuity order directly. If the stripes are broken and shifted relative to each other, the join is only \(G^0\); if the stripes touch but turn a sharp corner (a kink) at the seam, the surfaces meet with tangent continuity but a curvature jump, i.e. \(G^1\) but not \(G^2\); if the stripes flow across the seam smoothly with no kink and matched width, the join is \(G^2\) or better. Because the stripe pattern amplifies one derivative order of the normal field, it exposes exactly the defects that ordinary shading conceals.

## Isophotes

An isophote is a line of constant illumination on the surface. For a fixed light direction \(\mathbf{a}\) and unit surface normal \(\mathbf{n}(u,v)\), an isophote is the level set

\[
\{(u,v) : \mathbf{n}(u,v)\cdot\mathbf{a} = c\},\qquad c \text{ constant}.
\]

The key result behind their diagnostic power is that an isophote of a \(G^{k}\) surface is in general only \(G^{k-1}\) continuous: taking a level set of the normal field costs one order of smoothness. Consequently a surface that is \(G^1\) but not \(G^2\) produces isophotes with visible kinks, and a \(G^2\)-but-not-\(G^3\) surface produces isophotes with curvature jumps. Isophotes therefore act as an order-one magnifier of continuity defects and are a standard, lighting-independent check for surface fairness.

## Deviation

Deviation analysis compares the model against a reference (a target surface, a nominal CAD body, or a scanned point cloud or mesh) by measuring the signed distance from each sampled point to the reference along the local normal, then displaying it as a color map with tolerance bands. It answers a different question from zebra and isophotes, which probe intrinsic smoothness; deviation probes conformance to an external truth and is the basis for reverse-engineering fit assessment and inspection sign-off. All three are non-destructive quality overlays: they inform where to refine a surface, but they never modify it, which is why they belong to the analysis stage rather than the modeling stage of a surfacing workflow.
