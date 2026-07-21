Material-removal simulation checks what the *cutting edge* does; collision detection between the tool assembly, holder, and fixtures checks what the *non-cutting* geometry does. A cutter is only meant to engage the workpiece along its flutes; the shank, the tool holder, the spindle nose, clamps, vises, soft jaws, and locating fixtures are meant to keep clear. This class of check tests, at every point along the motion, whether any of those bodies interferes with the stock, the finished part, or another fixture, and flags contact that the program never intended.

## The interference test

Geometrically the problem is a **swept interference query** between a moving assembly and (mostly) static geometry. Two solids \(A\) and \(B\) interfere when their regularized intersection has non-empty interior, \(\mathrm{int}(A \cap B) \neq \varnothing\); a *clearance* query instead reports the minimum separation \(\delta = \min_{\mathbf{a}\in A,\ \mathbf{b}\in B}\lVert\mathbf{a}-\mathbf{b}\rVert\) so that near-misses within a safety margin can be surfaced, not just hard contacts. Testing this continuously along a path is expensive, so practical systems use a two-stage pipeline: a **broad phase** that quickly rejects body pairs whose bounding volumes cannot overlap, and a **narrow phase** that does exact overlap tests only on surviving pairs. The narrow phase almost universally relies on a **bounding-volume hierarchy** — a tree of nested boxes or spheres (oriented bounding boxes are a common choice for tight fit) — so that the cost of a query scales with the complexity near the contact rather than with the full model.

<svg viewBox="0 0 240 120" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1.5">
  <rect x="96" y="6" width="48" height="20"/>
  <text x="150" y="20" stroke="none" fill="currentColor" font-size="9">holder</text>
  <rect x="112" y="26" width="16" height="34"/>
  <text x="150" y="46" stroke="none" fill="currentColor" font-size="9">shank</text>
  <rect x="114" y="60" width="12" height="22"/>
  <text x="150" y="74" stroke="none" fill="currentColor" font-size="9">flutes (cut zone)</text>
  <path d="M20 92 h200"/>
  <rect x="70" y="82" width="100" height="10"/>
  <text x="22" y="108" stroke="none" fill="currentColor" font-size="9">stock / fixture below datum</text>
</svg>

## Distinguishing intended cutting from a real collision

The subtlety unique to machining is that *some* interference is expected: the flutes are supposed to be inside the stock, removing it. A naive overlap test would fire constantly. The correct model therefore separates the assembly into a **cutting portion** and a **non-cutting portion** and applies different rules. The cutting portion may enter the stock, but only up to the modeled flute length; the non-cutting portion (shank above the flutes, holder, spindle) must never touch stock or part except within a small allowed clearance. Contact by the shank or holder with the part is a **gouge by the holder**; contact with a clamp or fixture is a hard crash. A further distinction is made by motion type: interference during a cutting feed move is judged against the flute rule, whereas any interference during a **rapid / positioning** move is treated as a crash regardless of which part of the tool is involved, because rapids assume clear air.

## Where it matters

Holder and fixture collisions dominate failures in deep pockets, tall walls, and multi-axis work, where the part that clears the tip may still be struck by the wider holder as the tool tilts or plunges. The check drives concrete decisions: selecting a longer or slimmer holder, increasing tool stick-out (with the corresponding loss of rigidity), repositioning clamps, or choosing a lead/lean angle in five-axis work that keeps the holder off the surface. Because it reuses the same swept-motion machinery as machine-level interference checking, a well-built simulator treats tool-vs-part, holder-vs-part, and holder-vs-fixture as one interference framework applied to different body sets, with clearance thresholds tuned per pair.
