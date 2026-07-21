Geometric tolerances specify how much a real feature may deviate from its perfect nominal geometry, expressed as a **tolerance zone** — a region of space (between two planes, inside a cylinder, between two coaxial cylinders, or within a swept boundary) that all points of the toleranced feature must lie within. Unlike a plus/minus size limit, which only bounds a local dimension, a geometric tolerance bounds the *shape, orientation, or position* of the whole feature. The specification is carried in a **feature control frame**: a rectangular box reading, left to right, the characteristic symbol, the zone shape and size (a leading diameter sign for cylindrical zones), any material-condition modifier, and the ordered datum references that anchor the zone.

## The five families

The characteristics divide into families by how much reference they need:

- **Form** (straightness, flatness, circularity, cylindricity) constrains a single feature to itself and takes **no datum** — it says only "how perfect is this surface."
- **Orientation** (parallelism, perpendicularity, angularity) controls a feature's angle relative to a datum, so the zone's *tilt* is fixed but it may float in location.
- **Location** (position, and the legacy concentricity/symmetry) controls where a feature is relative to a datum frame.
- **Runout** (circular and total) controls a surface's deviation as the part is rotated about a datum axis, coupling form and location in one composite check.
- **Profile** (of a line, of a surface) is the most general: a uniform or unequally distributed boundary about the true profile that can control form alone, or form plus orientation plus location when datums are added.

## Position, material condition, and bonus tolerance

The workhorse is **position**, usually applied to features of size (holes, pins, slots) with a cylindrical zone whose axis is at the theoretically exact (basic) location. Its power comes from **material-condition modifiers**. At **maximum material condition (MMC)**, the tolerance stated in the frame is the minimum allowance; as the feature departs from MMC toward least material condition, that departure is added as **bonus tolerance**:

\[ t_{\text{bonus}} = \lvert d_{\text{actual}} - d_{\text{MMC}} \rvert, \qquad t_{\text{allowed}} = t_{\text{position}} + t_{\text{bonus}} \]

The unifying concept is the **virtual condition** — the constant worst-case boundary the feature may never violate. For an external feature at MMC,

\[ VC = d_{\text{MMC}} + t_{\text{position}}, \]

and for an internal feature (a hole) the geometric tolerance is subtracted. Because this boundary is fixed, mating parts can be verified with a simple fixed-size functional gauge, and it is exactly this boundary that propagates into assembly stack-up analysis. Runout, by contrast, is checked dynamically: **circular runout** limits full-indicator movement at each cross-section as the part spins about its datum axis (catching out-of-roundness and eccentricity), while **total runout** applies simultaneously over the whole surface (adding taper and profile error). Choosing the right characteristic means matching the tolerance to the *function*: form for sealing and bearing surfaces, orientation for mating faces, position for fastener patterns, runout for rotating shafts.
