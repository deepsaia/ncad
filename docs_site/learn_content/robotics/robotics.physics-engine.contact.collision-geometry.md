Before contact forces can be resolved, a simulator must answer two geometric questions for every pair of bodies: are they touching, and if so, where and how deeply. Doing this naively for \(n\) bodies is \(O(n^2)\) pair tests, each of which may itself be expensive on detailed meshes. Physics engines therefore split collision detection into a cheap **broad phase** that culls the pairs down to a small candidate set and an exact **narrow phase** that computes contact data only for survivors.

## Collision geometry

The shapes used for collision are usually *not* the visual meshes. Engines prefer analytic primitives (sphere, box, capsule, cylinder, plane) and convex hulls because closest-point and penetration queries on them are fast and numerically robust. Concave shapes are handled either as static triangle meshes (for terrain and environment) or by **convex decomposition** into a union of convex pieces, since most narrow-phase algorithms assume convexity. Some engines also support signed-distance fields (SDFs), which store the distance to the surface on a grid and make penetration depth and contact normals a direct lookup. Choosing coarse but tight collision proxies is a core modeling decision: it trades contact accuracy against solver cost and stability.

## Broad phase

The broad phase wraps each body in a conservative bound, typically an axis-aligned bounding box (AABB), and finds overlapping bounds quickly. Common structures are **sweep-and-prune** (sort AABB endpoints along axes and track overlaps incrementally, which exploits temporal coherence between frames), **uniform spatial hashing** (bucket bounds into grid cells), and **bounding-volume hierarchies** or dynamic AABB trees (log-time queries that scale to large, heterogeneous scenes). Any pair whose bounds do not overlap cannot collide and is discarded, cutting the workload from quadratic toward near-linear in typical scenes.

<svg viewBox="0 0 320 120" width="320" height="120" stroke="currentColor" fill="none" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg">
  <text x="10" y="14" fill="currentColor" stroke="none" font-size="11">broad phase: AABB overlap</text>
  <circle cx="60" cy="70" r="22"/>
  <rect x="38" y="48" width="44" height="44" stroke-dasharray="4 3"/>
  <rect x="78" y="52" width="40" height="40" stroke-dasharray="4 3"/>
  <rect x="84" y="58" width="28" height="28"/>
  <text x="200" y="14" fill="currentColor" stroke="none" font-size="11">narrow phase: contact</text>
  <circle cx="230" cy="70" r="22"/>
  <rect x="250" y="58" width="28" height="28"/>
  <circle cx="250" cy="70" r="2.5" fill="currentColor"/>
  <line x1="250" y1="70" x2="268" y2="70"/>
  <polygon points="268,70 262,66 262,74" fill="currentColor" stroke="none"/>
</svg>

## Narrow phase

For each surviving pair the narrow phase computes precise contact information: the closest points, the separation or penetration depth, and a contact normal, often aggregated into a **contact manifold** of several points so a flat resting contact is stable rather than jittering on one point. For convex shapes the workhorse is the **Gilbert-Johnson-Keerthi (GJK)** algorithm, which finds the minimum distance between two convex sets by searching their Minkowski difference; when the shapes interpenetrate GJK is paired with the **Expanding Polytope Algorithm (EPA)** to recover penetration depth and normal. The **separating-axis theorem (SAT)** provides an alternative for polyhedra. Robust manifold generation, contact caching (warm-starting the solver with last frame's contacts), and coherence exploitation are what make the narrow phase fast in practice.

## Where it matters

The collision pipeline sets both the performance ceiling and the contact quality of a simulation. A poor broad phase makes large scenes intractable; a poor narrow phase produces missing, duplicated, or noisy contacts that destabilize the constraint solver downstream. Practical engineering here is about matching geometry fidelity, bounding structure, and manifold strategy to the scene, and it interacts directly with the contact-solver and integrator choices, since the number and quality of contacts drive their difficulty.
