Top-down design only works if downstream geometry stays consistent with the upstream definitions it depends on. Two mechanisms make that possible: **published geometry**, which controls *what* one component exposes for others to reference, and **change propagation**, which controls *how* a change ripples through those references. Together they turn a web of inter-part dependencies into a disciplined, deterministic system rather than a tangle of fragile links.

## Published geometry

When one component needs to reference another, the naive approach is to let it pick any face, edge, or vertex it happens to need. This creates an uncontrolled parent-child link that breaks silently when the producer's internal topology is edited, and it is aggravated by the persistent-naming (topological-naming) problem, in which a reference bound to an incidentally-numbered face is invalidated when regeneration renumbers faces. **Published geometry** solves this by having the producing component explicitly designate a small, named set of interface entities, reference planes, curves, connection points, mating surfaces, that it commits to maintaining. Consumers may reference *only* the published set. The publication is effectively an interface contract: the producer is free to rework internals as long as the published entities keep their meaning, and consumers are insulated from churn they should not see.

## The dependency graph and propagation order

The references among features and components form a **directed acyclic graph**, with an edge from each referenced entity to the entity that depends on it. When something changes, the dependents must be re-evaluated in an order consistent with those edges, which is exactly a topological ordering of the DAG:

\[ u \to v \;\Rightarrow\; u \text{ is regenerated before } v. \]

Regeneration walks the graph downstream from the change, recomputing each affected entity after all of its inputs are current, so a controlling dimension edited on a skeleton drives the parts that reference it, which in turn drive whatever references them. Because a valid dependency structure must be acyclic, the system has to detect and reject cycles: a reference loop has no consistent evaluation order and would otherwise cause infinite or nondeterministic regeneration.

## Why it matters

Published geometry plus ordered propagation is what makes associativity trustworthy at assembly scale. It lets a single edit flow automatically to every dependent without manual rework, while the published-interface discipline keeps the dependency graph sparse and stable, reducing broken references and the coupling that makes large models brittle. The same principles underlie parametric constraint solving generally, where a change to one constrained value must propagate to all quantities derived from it in a well-defined, repeatable order.
