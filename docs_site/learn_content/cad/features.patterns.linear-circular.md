A **pattern** replicates geometry at regular positions so one authored feature drives many copies,
a **linear** pattern along one or two directions (a grid of holes), or a **circular** pattern about
an axis (a bolt circle, gear teeth, fan blades).

<figure markdown="span">
<svg viewBox="0 0 320 130" width="330" role="img" aria-label="Linear grid pattern and circular bolt-circle pattern" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2">
  <g fill="currentColor" stroke="none">
    <circle cx="30" cy="40" r="6"/><circle cx="70" cy="40" r="6"/><circle cx="110" cy="40" r="6"/>
    <circle cx="30" cy="80" r="6"/><circle cx="70" cy="80" r="6"/><circle cx="110" cy="80" r="6"/>
  </g>
  <text x="40" y="115" fill="currentColor" stroke="none" font-size="11">linear grid</text>
  <circle cx="250" cy="60" r="45" stroke-dasharray="4 3" opacity="0.5"/>
  <g fill="currentColor" stroke="none">
    <circle cx="250" cy="15" r="6"/><circle cx="289" cy="38" r="6"/><circle cx="289" cy="82" r="6"/>
    <circle cx="250" cy="105" r="6"/><circle cx="211" cy="82" r="6"/><circle cx="211" cy="38" r="6"/>
  </g>
  <text x="210" y="128" fill="currentColor" stroke="none" font-size="11">circular</text>
</svg>
<figcaption>A linear grid (left) and a circular bolt-circle (right) from one seed feature.</figcaption>
</figure>

## Count, spacing, and what gets copied

A linear pattern takes a direction, a spacing, and a count (optionally a second direction for a
grid); a circular pattern takes an axis, an angular step or total angle, and a count. A pattern
copies the *running result*, so it is placed after the feature(s) whose geometry it should
replicate.

Patterns can copy positive bodies or cut features. Because a pattern may change the body count
(disjoint copies), later ops must be prepared for a multibody result, or the copies must overlap to
fuse into one solid. Individual instances can usually be suppressed, dropping one hole from an
otherwise regular grid.
