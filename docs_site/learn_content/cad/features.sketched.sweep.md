**Sweep** moves a profile along a path curve to generate a solid, the feature for pipes, ducts,
handles, gaskets, and any part with a constant (or controlled) cross-section following a route. The
profile sits on a plane at the start of the path and is swept along it, staying normal to the path
by default.

<figure markdown="span">
<svg viewBox="0 0 300 150" width="320" role="img" aria-label="A profile swept along a curved path" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M 40 110 C 90 40 200 40 260 100" stroke-dasharray="5 4"/>
  <ellipse cx="40" cy="110" rx="10" ry="18"/>
  <ellipse cx="260" cy="100" rx="10" ry="18" opacity="0.6"/>
  <text x="120" y="35" fill="currentColor" stroke="none" font-size="11">path</text>
</svg>
<figcaption>A cross-section profile swept along a path curve, staying normal to it.</figcaption>
</figure>

## Path, orientation, and transitions

The path can be a 2D sketch or a 3D curve. Options control how the profile is carried: **keep
normal** to the path (the default) or **keep a fixed orientation**; how corners are handled
(**transition**: rounded, transformed, or right/mitered); and whether the profile scales or twists
along the way.

Sweep generalizes extrude (a sweep along a straight path) and underlies tubular and routed geometry.
The path must be smooth enough that the swept section does not self-intersect on tight bends, a
radius smaller than the profile pinches the solid, which the kernel rejects.
