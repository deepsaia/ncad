A **selector** picks topological entities by a **query over their attributes** rather than by
naming each one. Instead of listing four edges, an author writes `edges where orientation =
vertical` or `faces where type = cylinder`. The query re-evaluates on every rebuild, so it keeps
selecting the *right* set even as the model changes.

## Query, not enumeration

A selector is a rule: "all edges shorter than 2 mm", "the planar faces normal to +Z", "the edge
between the boss and the plate". It resolves against an **element map** that records each entity's
attributes (geometry type, orientation, size, provenance). Because the rule describes intent, adding
a fifth matching edge upstream automatically includes it, an enumeration would miss it.

## Why selectors matter for robustness

Selectors are the rule-based member of the reference family (alongside semantic names and generative
tags). They shine where the set is dynamic or large: fillet every vertical edge, chamfer every hole
rim, pattern onto every face of a kind. The risk is a query that is too broad (catching an unintended
edge) or too narrow (missing one after an edit), so a good selector language is precise and the
modeler reports what a query actually matched. Selectors turn "these specific edges" into "edges
that satisfy this property", which is far more durable across parametric change.
