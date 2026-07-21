Once a fixture is chosen, it becomes a solid obstacle that shares the work envelope with the moving tool, holder, and spindle. Treating **fixtures as collision bodies** means representing the vise, clamps, chuck jaws, soft-jaw blanks, and tombstones as static geometry that the toolpath must not intersect, exactly the same interference problem that motion and assembly analysis already solve. This reframing is powerful: fixture-collision checking is not a special CAM subsystem but a reuse of the general geometric-interference machinery that tests whether any two bodies overlap or come within a clearance threshold.

## Static overlap and swept motion

Two questions must be answered. First, at any single instant, does the tool assembly **overlap** a fixture body? This is a static intersection test between two solids. Second, over a motion, does the tool assembly's **swept volume** ever touch a fixture? A rapid move that clears at both endpoints can still slice through a clamp in between, so the whole trajectory must be considered, either by dense sampling of poses or by testing the continuous swept region. For a linear move of a body \(B\) from pose \(T_0\) to \(T_1\), the swept set is

\[ \text{sweep} = \bigcup_{s \in [0,1]} T(s)\, B, \qquad T(s) = \text{interp}(T_0, T_1, s), \]

and a collision exists if this set intersects any fixture solid. Because the tool is only *cutting* near the part and merely *transiting* elsewhere, clearance rules differ by segment: zero clearance is expected against the stock being cut, but a positive safety margin is enforced against clamps and the holder.

## Making the test tractable

Exact solid-solid intersection over a full toolpath is expensive, so practical checking layers cheap culls before exact tests. Each body is wrapped in a **bounding-volume hierarchy** (AABB, OBB, or sphere trees) so that most non-touching pairs are rejected by a fast overlap test; only the few surviving pairs run a precise query such as a convex-distance algorithm (GJK) that returns the minimum separation and hence the clearance margin. Reporting the **closest-point distance**, not just a yes/no hit, is what lets a planner shorten a tool, raise a retract plane, or reposition a clamp by a known amount.

The practical payoff is that verifying reach and safety against real workholding turns an abstract toolpath into a manufacturable one: gouge-free finishing, holder clearance in deep pockets, and rapid moves that route around clamps. Because the same distance and swept-volume queries drive assembly interference and mechanism motion studies, a single geometric-collision engine can serve process verification, kinematic simulation, and fixture design without duplicated code.
