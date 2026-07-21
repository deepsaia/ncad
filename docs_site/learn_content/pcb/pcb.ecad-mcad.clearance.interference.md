## Clearance and interference as an assembly query

Once the board and its components are lowered into a placed sub-assembly, checking that it fits inside its enclosure is an ordinary assembly interference query -- the same computation used for any mechanical assembly, now with the PCB assembly as one of the participants. Two distinct questions are being answered. *Hard interference* asks whether two solids overlap: the boolean intersection \(A \cap B\) has volume above a tolerance. *Clearance* (soft interference) asks whether the gap is smaller than a required minimum: the minimum distance
\[ d(A,B) = \min_{a\in A,\; b\in B} \lVert a-b\rVert \]
falls below a clearance threshold \(c\). Contact is the boundary case, where \(d\) is within a touch tolerance of zero.

For boundary-representation solids the minimum distance is found by searching closest-point pairs across the boundary elements (face-face, face-edge, edge-edge, and vertex cases), returning both the distance and the witness points that achieve it. For convex bodies this is what the classic distance algorithms such as GJK solve in the Minkowski-difference sense, where \(d(A,B)=\min\{\lVert w\rVert : w \in A \ominus B\}\) and overlap corresponds to the origin lying inside \(A\ominus B\). General non-convex board and enclosure shapes are handled by decomposing them into boundary features or into convex pieces and reducing to these primitive cases.

## Broad phase and narrow phase

Naive pairwise testing is \(O(n^2)\) in the number of bodies, which is prohibitive for a populated board with hundreds of components. The standard remedy is a broad-phase / narrow-phase split: cheap bounding-volume tests (axis-aligned or oriented boxes, or a bounding-volume hierarchy) prune the vast majority of pairs that cannot possibly clash, and the expensive exact distance or intersection runs only on the surviving candidates. Two boxes are provably disjoint the moment they are separated along any single axis, so most of the board's parts are eliminated against a distant wall in one comparison.

<svg viewBox="0 0 360 160" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" fill="none" stroke-width="1">
  <rect x="20" y="20" width="320" height="120"/>
  <rect x="60" y="110" width="240" height="8"/>
  <rect x="120" y="78" width="60" height="32"/>
  <line x1="150" y1="78" x2="150" y2="20" stroke-dasharray="3 3"/>
  <text x="158" y="52" font-size="10" stroke="none" fill="currentColor">headroom dz</text>
  <text x="120" y="134" font-size="10" stroke="none" fill="currentColor">board + component</text>
  <text x="26" y="16" font-size="10" stroke="none" fill="currentColor">enclosure wall</text>
</svg>

For the enclosure fit specifically, the dominant checks run above and around the board. The headroom over the tallest component is \(\Delta z = H_{\text{inner}} - (z_s + h_{\max})\), where \(h_{\max}\) is the tallest body's height above the seating surface; a negative value is a clash and a small positive value a clearance-margin violation. Lateral checks confirm the board edge clears the walls and standoffs and that connectors, switches, and indicators line up with -- and clear -- their cutouts. To keep this fast and numerically stable, components are frequently reduced to height/keepout envelopes (bounding cylinders or boxes carrying the maximum height), so a first-pass fit study runs on a handful of simple solids rather than full component geometry.

Results are categorized so a designer can triage them: penetration (report the intersection volume and a representative penetration direction), contact within tolerance, and clearance-margin violations (report the gap and the witness points so the offending features can be located). Because the query is deterministic on a fixed assembly state, it doubles as a regression check: re-running it after a layout or enclosure change flags any newly introduced clash or lost margin before the two disciplines diverge.
