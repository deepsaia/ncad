**Assembly degrees of freedom** measure how a mated assembly can still move. A free rigid body in
space has 6 DoF (3 translation, 3 rotation); each mate removes some, and the remaining count tells
whether the assembly is fully located, still movable, or over-constrained, the 3D analogue of sketch
DoF.

\[
\text{DoF} = 6\,(n - 1) - \text{rank of the constraint Jacobian},
\]

where $n$ counts parts including ground (the grounded part removes the assembly's own 6 DoF). A
**well-constrained** assembly has zero remaining DoF (every part fixed); a mechanism *deliberately*
retains DoF (a hinge keeps 1 rotational freedom); **over-constrained** means conflicting mates the
solver cannot satisfy; **redundant** means a mate that duplicates one already implied.

## Why the count is diagnostic

The DoF report is a legibility layer over the assembly solve, computed from the constraint
Jacobian's rank, just like a sketch. It tells the author *why* a part will or will not move and
which mates are responsible. Crucially, retained DoF are not errors: a mechanism's free DoF are
exactly what motion drives. The report distinguishes an intended freedom (a joint's DoF) from an
accidental under-constraint, and flags conflicts and redundancies with the offending mate, so the
assembly behaves predictably before any motion is applied.
