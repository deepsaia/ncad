A **connect** places an instance by landing one of its connector frames exactly onto a connector
frame of an already-placed instance. It is the fast, robust way to position parts: instead of
computing a transform by hand, name two connectors and the assembler snaps them together.

## How the snap works

Connecting frame $F_a$ (on the moving instance) to frame $F_b$ (on a placed target) computes the
rigid transform that maps $F_a$ onto $F_b$: the rotation aligning their axes plus the translation
aligning their origins. The moving instance is placed by that transform, so its connector coincides
with the target's, origin on origin, axes aligned.

## Why it is robust

Connect references *connectors*, not raw geometry, so it survives edits to either part (the
connectors move with their parts through rebuilds). It composes naturally: place the first instance,
then connect the next onto it, then the next, building the assembly as a chain of snaps. An optional
offset or flip adjusts the landing (seat a bolt with a gap, flip a bracket). Connect is placement
that expresses *intent*, "this tip sits on that pivot", rather than a brittle absolute transform,
which is exactly what keeps a positioned assembly correct as its parts evolve.
