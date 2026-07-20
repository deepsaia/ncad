**Loft** blends a solid through an ordered series of profile sections placed on different planes,
the feature for transitions and organic shapes: a round-to-square duct adapter, a boat hull, a
turbine blade, a bottle shoulder. The kernel builds a surface skin passing through each section in
order, then caps the ends into a solid.

<figure markdown="span">
<svg viewBox="0 0 300 150" width="320" role="img" aria-label="A solid lofted through three profile sections" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <rect x="30" y="45" width="40" height="60"/>
  <ellipse cx="150" cy="75" rx="16" ry="30"/>
  <circle cx="255" cy="75" r="24"/>
  <line x1="70" y1="45" x2="140" y2="48" opacity="0.5"/>
  <line x1="70" y1="105" x2="140" y2="102" opacity="0.5"/>
  <line x1="164" y1="52" x2="235" y2="55" opacity="0.5"/>
  <line x1="164" y1="98" x2="235" y2="95" opacity="0.5"/>
</svg>
<figcaption>Three sections (rectangle, ellipse, circle) blended into one lofted solid.</figcaption>
</figure>

## Sections, guides, and continuity

Sections are profiles (often on parallel planes, but not required). A loft can be **ruled** (straight
blends between sections) or **smooth** (a fair curve through them); **guide curves** steer the skin
between sections; and end conditions control tangency so a loft meets an adjacent face smoothly.
Point caps let a loft taper to a vertex (a cone-like end).

Loft is the most shape-sensitive sketched feature: section count, ordering, and vertex alignment all
affect the result, and mismatched sections can twist the skin. It is where sketched modeling reaches
toward freeform surfacing.
