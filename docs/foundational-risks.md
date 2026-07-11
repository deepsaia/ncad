# Foundational risks (living audit)

Risks in the core spine that could impede scaling to professional-grade CAD (NX / Creo /
Solid Edge / Fusion / Parasolid). This is a **living document**: when a bucket touches one of
these, resolve it and update the status here; when a new foundational risk is found, add it.

Scope note: **backward compatibility is not required** - old examples/gate fixtures/golden
signatures may be regenerated when a foundational change lands. Prefer the clean, uniform
design over compatibility shims. (This removes a major constraint: e.g. the multibody model
need not keep the single-shape code path byte-identical.)

---

## R1 - Element provenance carry-forward is geometric (topological naming)

**What:** `ElementMap._geometric_key` matches a surviving face/edge across a feature by
rounded centroid + size (4 dp). A face that moves more than the rounding loses its identity;
symmetric/repeated features can alias. This is the classic topological-naming problem.

**Impact:** high. Persistent references (`pad.cap(+Z)`, selectors) are only as stable as this
key. At scale (patterns, moved features, mirrored geometry) it will mis-attribute or drop
identity.

**Correct fix:** the Phase 4 persistent-name layer (content/topology-hash naming, design
section 2, Q2). Explicitly out of scope before Phase 4; the code already says so.

**Guard meanwhile:** do NOT build new persistent identity on top of this key. Bucket 3.0 body
ids are feature-derived and born-once, not geometric - correct. Keep it that way.

**Status:** open, scheduled for Phase 4.

## R2 - Instance identity is positional-by-geometry

**What:** `ElementMap.instance(feature_id, index)` returns the index-th element by a geometric
sort key. `holes.instance(0)` means "first by centroid sort," not a stable instance id. Suppress
one instance and the indices shift.

**Impact:** medium-high, hits pattern buckets directly. Professional tools give each pattern
instance a stable identity (suppress/skip/reference by instance).

**Correct fix:** bucket 3.2 (patterns) - pattern instances get explicit stable ids, not
geometric-sort positions. The Phase 3 design principle "instances are addressable" already
commits to this.

**Status:** closed in 3.2. Pattern instances are addressable by born-once ordinal body
ids (`<feature>/body/<n>`); `ElementMap.instance` resolves by that stable ordinal, so
suppressing one instance no longer renumbers the rest. Single-body features keep the
legacy centroid order.

## R3 - Kernel has no mass-properties / material abstraction

**What:** the Kernel ABC exposes `volume`/`bounding_box`/`signature` but no mass, COG (as a
property), or material-derived quantities.

**Impact:** low - cleanly additive.

**Correct fix:** bucket 3.5 (per-body material data + derived mass properties).

**Status:** closed in 3.5. Mass/material is a layer OVER the kernel (`MaterialLibrary` +
`MaterialResolver` + `MassCalculator`): the kernel stays geometry-only (`volume` + `signature`
cog), and density (document/material data) drives derived mass = density x volume, computed on
demand. No density in the kernel.

## R4 - Element is a mutable record with a mutated attrs dict

**What:** `Element` is a plain (non-frozen) class and `ElementMap.rebuild` mutates `attrs`
in place (`attrs["created_by"] = ...`). Works today, but mutable identity records are a
latent aliasing/determinism hazard as the map and its consumers grow.

**Impact:** low. Tidy opportunistically (freeze `Element`, build attrs immutably) when next
editing the element map.

**Status:** open, low priority.

## R5 - Single-shape-per-feature model (addressed by Phase 3)

**What:** every feature produced one shape; no notion of multiple bodies.

**Impact:** was foundational - blocked multibody, per-body props, body algebra.

**Fix:** bucket 3.0 introduces the `BodySet` model (first-class persistent body identity,
body kind, per-body provenance, merge scope).

**Status:** in progress (bucket 3.0).

---

## How to use this doc

- Before a bucket, check whether it touches a risk here; if so, its plan should resolve or
  explicitly defer it (with the reason).
- When a fix lands, update the risk's **Status** (and link the bucket/PR).
- When a new foundational risk surfaces, add it with What / Impact / Correct fix / Status.
- Pair with `docs/feature-ordering.md` (op-sequence rules) - that is about *using* the ops;
  this is about the *soundness of the model* underneath them.
