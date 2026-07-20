**Persistence** is the guarantee that a reference resolves to the same intended entity across
rebuilds and upstream edits. It is the property that makes semantic names, generative tags, and
selectors trustworthy: a reference is only useful if it *stays attached*.

## The element map

Persistence is implemented by an **element map**: a per-build record that maps each topological
entity (face, edge, vertex) to a stable identifier derived from its construction lineage plus the
attributes a selector can query. On rebuild, replay reconstructs the map deterministically, so a
reference stored as a lineage-based id finds its entity again even though the kernel's raw numbering
changed.

## Cost and scope

The map is held only for parts **under active edit** and cached alongside the geometry; lightweight
or simplified representations (used in large assemblies) carry no map. Its size is bounded by part
topology, an intentional budget, so it does not balloon on imported or highly-featured parts.

Persistence is the answer to the topological naming problem. When it holds, editing an upstream
feature reliably updates everything built on it; when a reference genuinely cannot resolve (its
entity was removed), the modeler surfaces an id-attributed error rather than silently reattaching.
This is the difference between a parametric model that survives editing and one that quietly
corrupts itself.
