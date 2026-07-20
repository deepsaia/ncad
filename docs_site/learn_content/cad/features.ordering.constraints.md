Because a feature tree is an ordered pipeline over an order-sensitive geometry kernel, some
operations **must** precede or follow others. These **ordering constraints** are not style
preferences, violating them yields wrong geometry, an invalid B-rep, or a kernel crash.

## Recurring rules

- **Base dress-up before complexity.** Shell, fillet, and draft the base solid while it is a simple
  prism, before booleans, holes, bosses, and ribs complicate the topology. A late shell
  self-intersects; a late fillet can segfault the kernel.
- **Fillet before draft.** A draft tapers walls, so a "vertical edge" selection made *after* a draft
  finds nothing. Round first, taper second.
- **Producers before consumers.** A feature that references topology (a fillet on an edge, a wrap on
  a face, a pocket to a face) must come after the feature that *creates* that topology.
- **Patterns and mirrors after their source.** They copy the running result, so the geometry they
  replicate must already exist.
- **Single-solid before whole-body ops.** Draft and some dress-up need one solid; a rib or boolean
  that leaves two disjoint bodies must be fixed first.

## Why the modeler enforces the safe order

The kernel cannot always catch a bad order gracefully (a crash is not a catchable exception), so the
robust discipline is to author in the manufacturing-like order, rough stock, base dress-up, then
features, and to record each learned constraint. A modeler surfaces the failure with the offending
feature id rather than producing silently wrong geometry.
