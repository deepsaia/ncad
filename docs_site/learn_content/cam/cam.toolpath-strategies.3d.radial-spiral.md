Radial and spiral finishing are pattern-based 3D strategies that project a planar guide curve onto the target surface and drive the tool along it. In **radial** machining the guide is a fan of straight rays emanating from a common center point; in **spiral** machining it is a single continuous Archimedean spiral wound outward (or inward) from that center. Both are chosen when the part has an approximately circular boundary or a natural pole, such as a round cavity, a hemispherical dome, a lens, or a rotationally biased pocket.

Radial patterns share the classic weakness of any converging path: the passes crowd together near the center and spread apart at the rim. The angular stepover \(\Delta\phi\) produces a physical stepover \(s(\rho) = \rho\,\Delta\phi\) that grows linearly with radius \(\rho\). To hold a target finish, \(\Delta\phi\) must be chosen for the **outer** radius, which means the center is massively overmachined (huge dwell, tool wear, and burnishing at the pole). Spiral patterns cure this by holding a constant radial pitch \(p\) per revolution, giving a near-constant stepover \(s \approx p\) independent of radius, and, crucially, a **single continuous path** with no retract-and-reposition between passes.

An Archimedean spiral in the guide plane is

\[ \rho(\phi) = \frac{p}{2\pi}\,\phi, \qquad s = \rho(\phi + 2\pi) - \rho(\phi) = p, \]

so the radial advance per turn is the pitch and the resulting scallop is set by \(p\) through the usual ball-nose cusp relation \(h \approx r - \sqrt{r^2 - (p/2)^2}\). The continuity of the spiral eliminates the feed marks and acceleration transients that a raster or radial pattern leaves at every direction reversal, which is why spiral finishing gives visibly smoother round surfaces.

## Practical considerations

The pole is the trouble spot for both. On a spiral, near the center the tool sweeps a tiny circle at high angular rate, so feed must be clamped to respect the machine's velocity limits; a small \(\rho\) with fixed surface feed implies large \(\dot\phi\). On steep or vertical walls the projection of a flat spiral stretches badly, so these strategies target shallow, bowl-like, or domed regions and are combined with waterline on the steep bands. When the pole itself must be finished, implementations add a small point-cap move or blend the spiral into a hemispherical scallop path. Radial remains useful for spoke-like features and for deliberately orienting the tool-mark texture, but spiral is the default for continuous finishing of round forms.
