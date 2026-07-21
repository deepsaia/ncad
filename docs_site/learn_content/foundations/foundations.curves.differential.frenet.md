The **Frenet-Serret frame** (also called the TNB frame or moving trihedron) is an orthonormal coordinate system attached to a curve and carried along it, giving a local, curve-following reference at every point. It converts a curve's shape into the motion of a small rigid frame, which is why it underlies sweeping, tubing, and camera-path construction.

For a regular curve parameterized by arc length \(s\), the three unit vectors are defined in sequence:

\[ \mathbf{T} = \frac{d\mathbf{C}}{ds}, \qquad \mathbf{N} = \frac{d\mathbf{T}/ds}{\lVert d\mathbf{T}/ds \rVert}, \qquad \mathbf{B} = \mathbf{T} \times \mathbf{N}. \]

Here \(\mathbf{T}\) is the **unit tangent** (direction of travel), \(\mathbf{N}\) is the **principal normal** (points toward the center of the osculating circle, the direction the curve is bending), and \(\mathbf{B}\) is the **binormal** (perpendicular to the local plane of the bend). The plane spanned by \(\mathbf{T}\) and \(\mathbf{N}\) is the osculating plane; \(\mathbf{N}\) and \(\mathbf{B}\) span the normal plane.

<svg viewBox="0 0 260 150" width="260" height="150" stroke="currentColor" fill="none" stroke-width="1.5" aria-label="Frenet TNB frame on a curve">
  <path d="M20 120 Q 90 20 170 70 T 240 40"/>
  <circle cx="120" cy="57" r="3" fill="currentColor"/>
  <line x1="120" y1="57" x2="170" y2="52"/>
  <text x="172" y="52" font-size="11" stroke="none" fill="currentColor">T</text>
  <line x1="120" y1="57" x2="128" y2="105"/>
  <text x="130" y="110" font-size="11" stroke="none" fill="currentColor">N</text>
  <line x1="120" y1="57" x2="92" y2="33"/>
  <text x="78" y="30" font-size="11" stroke="none" fill="currentColor">B</text>
</svg>

## The Frenet-Serret formulas

The power of the frame comes from how it evolves along the curve. Its derivatives are expressed back in terms of the frame itself, coupled only through curvature \(\kappa\) and torsion \(\tau\):

\[ \frac{d\mathbf{T}}{ds} = \kappa\,\mathbf{N}, \qquad \frac{d\mathbf{N}}{ds} = -\kappa\,\mathbf{T} + \tau\,\mathbf{B}, \qquad \frac{d\mathbf{B}}{ds} = -\tau\,\mathbf{N}. \]

Read physically, curvature turns the frame within the osculating plane (\(\mathbf{T}\) toward \(\mathbf{N}\)), while torsion rotates the frame about the tangent (tilting \(\mathbf{N}\) and \(\mathbf{B}\)). The skew-symmetric structure of these equations guarantees the frame stays orthonormal as it moves, and together with the fundamental theorem of curves they show that \(\kappa(s)\) and \(\tau(s)\) fully determine the curve up to placement in space.

The Frenet frame has an important **degeneracy** that every practical implementation must handle: the principal normal \(\mathbf{N}\) is undefined wherever \(\kappa = 0\), that is, at straight segments and inflection points, because there is no bend direction to point to. As the curve passes through an inflection, \(\mathbf{N}\) and \(\mathbf{B}\) can flip abruptly, causing a swept profile or extruded tube to twist or pinch. For this reason geometric modeling often prefers a **rotation-minimizing frame** (a parallel-transport frame), which advances the normal with the least possible rotation about the tangent and remains well defined even where curvature vanishes. Choosing between the natural Frenet frame and a rotation-minimizing frame is the standard design decision when generating swept solids, pipes, ribbons, and animation paths.
