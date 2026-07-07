# Blender: transferable architecture ideas for ncad

Blender is a **mesh** DCC tool, not a B-rep CAD engine, so none of its *geometry* transfers
(ncad stays on OCCT/build123d, §4). But several of Blender's **architectural** patterns map
cleanly onto ncad's own design, and some of them are things ncad is already reinventing.
This note is about those patterns, not about meshes or rendering.

Scope boundary against the two existing Blender-adjacent notes:
- [[infinigen-transferable-ideas]] already covers the **node system + transpiler** layer
  (parametric-by-default authoring, the visual-graph-to-code idea). Not repeated here.
- design §13/§17 already position Blender as a **render backend / viewer influence**, not a
  plugin core. This note is the *engine-architecture* reading that sits alongside those.

Facts below are drawn from Blender's developer docs / manual (GPL project); the "transfer
to ncad" reasoning is architectural judgment against `design.md`.

---

## 1. The modifier stack = a non-destructive feature tree (validation, not novelty)

Blender's **modifier stack** is an ordered, non-destructive pipeline over base mesh data:
the original mesh (the *original ID*) is never mutated; modifiers are applied in order to
produce a separate *evaluated* result (`obj.evaluated_get(depsgraph).data`). You can
reorder, toggle, and edit any modifier and the stack re-evaluates from the untouched base.

**Transfer to ncad.** This is *exactly* ncad's ordered feature tree with a pure
`build(document) >> model` (§0), and Blender's "original vs evaluated ID" split is the same
discipline as ncad's "document is the source of truth; geometry is an output" (§0 corollary).
So the takeaway is **validation, not a new idea**: one of the most successful open 3D tools
independently arrived at ncad's central decision (never mutate the source, always
re-evaluate). The one concrete lesson is the **original/evaluated split as an explicit API
boundary** — Blender exposes both the authored data and the evaluated proxy; ncad should
keep that boundary equally crisp (the document vs. the built B-rep, never conflated).

## 2. The dependency graph (depsgraph) = incremental rebuild, done at scale

Blender's **depsgraph** builds a **DAG of all data-blocks and their relationships** and
evaluates them in correct topological order. Its load-bearing property is **dirty-flag
incremental evaluation**: only data flagged dirty is recomputed, and changes propagate along
dependency edges rather than triggering a full-scene rebuild (`evaluated_depsgraph_get()`
"forces an evaluation if anything is dirty"). Drivers and constraints are recorded *as graph
edges*, so when a driving value changes, dependents re-evaluate in order.

**Transfer to ncad.** This is the mature version of ncad's **rebuild graph + content-addressed
cache** (§4). ncad already resolves parameters/references into a topological order and
re-executes only the dirty suffix; Blender is proof that this pattern scales to huge scenes
and is the right backbone. Two specific things worth stealing:
- **Dependencies as first-class graph edges**, including *parametric* ones (a driver = an
  edge). ncad's expression layer (`${ref}`, §1) and reference resolver (§2) already imply
  these edges; making them explicit graph edges (as the depsgraph does) is what lets
  invalidation be precise rather than conservative, echoing the Infinigen
  `evict_memo_for_obj` idea in [[infinigen-transferable-ideas]].
- **A construction-time constraint Blender documents honestly:** "we have to know all the
  pointers evaluation functions deal with at graph construction time." ncad's analogue is
  that the rebuild graph must know a feature's full input set (params + resolved refs)
  *before* executing it, which is exactly what the content-addressed cache key already
  hashes (§4a). Blender validates that this is the correct and sufficient design.

## 3. Fields = lazily-evaluated functions over a geometry domain

Blender's Geometry-Nodes **fields** are "not buckets of values, but operations on data" —
a field is a **lazily-evaluated function bound to a domain** (points / edges / faces),
evaluated per-element against attribute data (position, normal, computed values), not a
materialized array.

**Transfer to ncad.** This is the right mental model for ncad's **selector layer** (§2):
`select edges where convexity = 'convex' and length > 10` is *precisely* a field, a lazy
predicate evaluated per-element against a versioned attribute model. ncad already frames
selectors this way; Blender's fields validate that "attribute model + lazy per-element
function" is the durable design, and suggest the natural extension, **computed/derived
attributes** (normal, area, curvature as queryable fields), which ncad's attribute model
(§2, Q4) should treat as first-class alongside stored ones. The distinction Blender draws,
*stored* attributes vs *derived* fields, is a useful one for ncad to adopt explicitly.

## 4. Data-blocks + linking + library overrides = instances and in-context design

In Blender an asset "is almost never a single data-block, but a group of data-blocks with
dependency relationships." Objects **reference shared data-blocks**; a **linked** (external)
asset can be **locally overridden** by layering deltas onto the linked hierarchy (a
"library override"), the basis of a non-destructive link-and-override pipeline.

**Transfer to ncad.** Two direct maps:
- **Data-block references >> assembly instances (§7).** ncad's assembly is "instances of
  parts" referenced by name; Blender's data-block-reference model (many objects sharing one
  mesh data-block) is the same instancing discipline, and its dependency-hierarchy view is
  how ncad's large-assembly reps (§7) should reason about what to load.
- **Library override >> top-down / in-context edits and part variants.** Blender's "link a
  shared asset, then layer local deltas" is a concrete pattern for ncad's **skeleton /
  master-model** propagation (§7) and for part *configurations/variants* (a shared base
  document with per-instance overrides). Worth noting Blender's own caveat: **override
  persistence has edge cases across data types** (weights lost on reopen) — the lesson is
  that an override system needs a *typed, tested* delta model, not an ad-hoc patch, which
  fits ncad's validated-dict-patch mutation surface (§12).

## 5. Viewer UX conventions (a smaller, concrete borrow)

Blender's viewport conventions, object **pick/select by id**, a persistent side panel
(N-panel) of properties for the selection, draggable **gizmos** for orientation/transform,
are the interaction vocabulary a good 3D viewer converges on. ncad's viewer already has
pick-by-id, a data sidebar, and an orientation gizmo (bucket 0.3 / cross-cutting viewer
track), so this is **convergent validation** again rather than a new requirement, but
Blender is the reference for the interaction grammar (hover-highlight, selection-driven
side panel, snap-to-edge gizmos) as ncad's viewer grows toward measurement, PMI, and motion
playback (§13).

---

## Summary

| Blender pattern | ncad analogue | Verdict |
|-----------------|---------------|---------|
| Modifier stack (non-destructive, re-evaluatable) | Ordered feature tree, pure `build` (§0) | Convergent validation; keep the original/evaluated boundary crisp. |
| Depsgraph (dirty-flag incremental DAG) | Rebuild graph + content-addressed cache (§4) | Steal: dependencies (incl. parametric) as explicit graph edges for precise invalidation. |
| Fields (lazy per-element functions) | Selector layer over attribute model (§2) | Steal: treat derived attributes (normal/area/curvature) as first-class queryable fields. |
| Data-blocks + library override | Assembly instances + skeleton/in-context (§7) | Steal: a *typed, tested* override/delta model for part variants and master-model propagation. |
| Viewport pick / N-panel / gizmos | Viewer pick-by-id + sidebar + gizmo (§13) | Convergent; Blender is the interaction-grammar reference. |

**Confidence:** medium-high on the architecture facts (depsgraph DAG + dirty evaluation,
original/evaluated split, fields-as-functions, data-block/override model, all from Blender's
own docs); the "transfer" column is architectural judgment. **Biggest takeaway:** the two
patterns Blender does at scale that ncad is still building, **precise dependency-edge
invalidation** (depsgraph) and a **typed override/delta model** (library overrides), are the
ones worth studying most closely when ncad hardens incremental rebuild (§4) and reaches
assemblies (§7). Everything else is convergent validation that ncad's core decisions match a
proven open 3D tool. **Not transferable:** anything geometric, Blender is mesh; ncad is
B-rep.
