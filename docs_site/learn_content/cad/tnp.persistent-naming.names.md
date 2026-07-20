The **topological naming problem** (TNP) is the central hazard of history-based CAD: when a feature
references a face or edge, and an upstream edit changes the model's topology, the reference must
still resolve to the *intended* geometry, even though the kernel may have renumbered every face.

A naive kernel identifies faces by index (face #7). Insert a feature upstream and #7 now denotes a
different face; every downstream reference silently attaches to the wrong geometry. That is the TNP,
and it is why robust parametric modeling needs **persistent names**.

## Persistent naming

A persistent name identifies a topological entity by its **construction lineage**, how it came to
exist, rather than its position in the current numbering. A face is "the cap created by extrude
`pad`" or "the face split from the top by boolean `cut`". Because the name derives from the
operations that produced the entity, it survives rebuilds and upstream edits: replay reconstructs
the same lineage and the name resolves to the same face.

This is the load-bearing layer beneath every reference in the model, fillets on edges, sketches on
faces, joints on connectors, PMI on features. Without it, replay could not reliably reattach
features, and the whole edit-and-rebuild premise of parametric CAD would be unsound. Getting it
right is what separates a toy history modeler from a production one.
