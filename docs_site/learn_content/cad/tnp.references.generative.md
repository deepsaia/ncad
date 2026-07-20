A **generative reference** names a topological entity by the **role it plays in the operation that
created it**, tagged at the moment the op mints it. When an extrude produces a solid, its new faces
are tagged by role: the `cap(+Z)` and `cap(-Z)` end faces, the `side` walls. A later feature can
then reference "the +Z cap of `pad`" and resolve it every rebuild.

## Why ops tag their own output

Some faces do not exist until an operation creates them, so they cannot be named by a pre-existing
selection. The op that creates them is the only place that knows their role, so it stamps a
**generative tag** as it builds. This makes brand-new geometry referenceable immediately: the cap of
a fresh extrude, the wall left by a shell, the fillet surface between two faces.

Generative tags are deterministic: the same op on the same input always assigns the same tags, so
the reference is stable across rebuilds (the persistent-naming guarantee). They complement semantic
references (which name existing entities by construction lineage) and selectors (which pick entities
by a query): generative tagging is how the *producer* labels what it makes, so *consumers*
downstream can find it by role rather than by a fragile index.
