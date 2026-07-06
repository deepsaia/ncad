# Infinigen: transferable ideas for ncad

A study of [Infinigen](https://infinigen.org) (Princeton VL, procedural photorealistic
world generator on Blender) read against ncad's design. Unlike the other notes here,
this is **not** a sourced decision behind design §19; it is a comparative reading of an
external codebase (`~/exp/infinigen`, read at its then-current checkout) to extract ideas
that map onto ncad's generator, constraint, and determinism layers. File:line references
below point into the Infinigen tree, not ncad.

Infinigen is the clearest real-world example of the **"code produces the model, run it to
get geometry"** family that design §18's generative north-star targets: a seed + config
deterministically drives Python that builds a scene, renders it, and emits dense ground
truth. Its substrate is Blender/mesh, not an exact B-rep kernel, so the geometry engine
does not transfer; the *patterns* around it do.

Three subsystems are worth mining, in priority order for ncad.

---

## 1. Parametric-by-default authoring (from the node transpiler)

**What Infinigen does.** Infinigen authors shader/geometry-node graphs visually in
Blender, then *transpiles* them to reproducible Python that rebuilds the graph via a
`NodeWrangler` builder (`infinigen/core/nodes/node_transpiler/transpiler.py`). Three
mechanics matter independent of Blender:

- **Distributions as first-class values.** A node labelled `radius ~ U(1,3)` emits the
  source `uniform(1.0, 3.0)`, so the artifact carries a *live randomized expression*, not
  a frozen number (`represent_label_value_expression`, `transpiler.py:310-393`; only
  `U/uniform`, `N/normal`, `R/randint`, exactly two args). Re-running the emitted code
  re-samples.
- **Default-diffing for terseness.** It spawns a pristine node of the same type, diffs the
  real node against it (vector-safe `np.all(a==b)`), and serializes **only attributes that
  differ from the factory default** (`has_default_value_changed`, `:230-270`). This is the
  whole "keep output diff-friendly" strategy.
- **DAG memoisation.** Each node is emitted once, keyed by identity; a node feeding two
  places returns its existing variable + empty code, topologically ordered
  (`create_node`, `:673-749`).
- **Data vs. reconstruction split.** Nested data (curve points, colour-ramp stops) is
  emitted as a compact *data literal* plus a call to a hand-written runtime helper
  (`assign_curve`), never as inline step-by-step construction (`:273-431`).

**Transfer to ncad.**
- **Parametric-by-default document fields** are the highest-value steal, and they are just
  design §1 ("refs + registered-function calls, logic in code") extended to distributions:
  a HOCON value may be a distribution resolved by a **registered function** against a
  seeded RNG at *authoring* time. Do it with structured keys (`{dist: "uniform",
  args: [1, 3]}`), **not** the `~`-in-string hack, which exists only because Blender nodes
  lack a metadata field; ncad has real keys.
- **Default-diffing transfers directly and is cleaner in ncad:** use `inspect.signature`
  defaults (or the JSON schema) as the baseline and serialise only non-default keys, for
  diff-friendly round-tripping. No "spawn temp node then delete" needed. Copy the
  vector-safe compare for CAD numeric params (points, vectors, transforms).
- **Memoisation maps onto incremental rebuild**, keyed on the stable `id`/document path
  (ncad already has stable ids, §0), dropping Blender's fragile `.NNN`-suffix parsing.
- **Data-vs-helper split** maps to: a spline / variable-radius fillet serialises as a
  compact data literal + a registered builder, not construction steps in the document.
- **Does not carry:** the visual-editor round-trip is the transpiler's entire reason to
  exist, and ncad has *no authoring GUI by design* (§17). The transpiler-as-such is moot;
  its *output discipline* (deltas-only, reproducible, memoised) is what a good HOCON
  serialiser should do.

---

## 2. A declarative constraint graph, and the exact-vs-soft split

**What Infinigen does (indoor layout, `infinigen/core/constraints/`).** A Python-embedded
DSL builds an **immutable, inspectable expression graph** via operator overloading, then a
**simulated-annealing** solver optimises it against a trimesh scene.

- **Deferred graph, not evaluation.** Operators build nodes: `scene()[Chair]
  .related_to(table, on).count()` is a 4-level tree. `__bool__` *throws*
  (`constraint_language/types.py:12-26`), forcing `*`/`+` over Python's `and`/`or`;
  comparisons (`==`, `>=`) return predicate nodes carrying an `operator.*` callable.
  `.minimize(weight)` is just `self * constant(weight)`.
- **Lexicographic acceptance** (`metrop_hastings_with_viol`, `example_solver/annealing.py:227-250`):
  hard-constraint violation count is the *primary* key. A move that reduces violations is
  accepted unconditionally; a move that increases them is rejected unconditionally;
  Metropolis-Hastings on soft loss applies **only on a tie**. Not a weighted penalty sum:
  a preference can never trade away a real constraint.
- **Graded violations** (`viol_count`, `evaluator/evaluate.py:140-193`): a hard `in_range`
  returns the *signed distance outside the band*, not 0/1, giving a gradient even while
  violated. The same node is binary as a bool, graded as a hard constraint.
- **Domain-scoped incremental re-eval** (`evict_memo_for_obj`, `eval_memo.py:82-105`):
  one persistent memo across the anneal; after a move, evict only entries whose object-set
  domain could contain the moved object. Move one chair >> only subtrees mentioning it
  recompute.
- **Exact DOF via least-squares** (`geometry/dof.py:202-256`): parent-face-plane
  constraints become linear equations; `np.linalg.lstsq` gives `dof = 3 - rank`, exactly
  the residual translational freedom. The null space *is* the joint's motion.

**Transfer to ncad.** ncad already owns an *exact* geometric constraint solver (py-slvs,
§5) and plans a 3D assembly/joint solver (§7-8). The two regimes must stay separate:

- **Exact (ncad today + planned joints):** coincidence / distance / angle / tangency /
  mates solved to residual 0; **DOF = Jacobian null space**. Infinigen's `lstsq` rank trick
  is the same math at single-object granularity, and validates ncad's plan to surface joint
  DOFs as motion.
- **Soft (optional future layer):** "prefer centred," "minimise travel," "auto-arrange N
  parts" >> a scalar score graph + **feasibility-first lexicographic** optimisation. Use
  annealing *only* here, never for real mates.
- **The declarative graph DSL is backend-agnostic and the most portable idea:** a
  `__bool__`-guarded, operator-overloaded, deferred constraint graph is *one inspectable
  representation* feedable to either py-slvs (exact) or a scorer (soft). It lets a HOCON
  predicate like `distance(a,b) >= 5` parse into an inspectable node, not an opaque
  callback.
- **Graded residuals >> diagnostics:** even in an exact solver, report *signed residuals*
  ("this distance is 0.3 short"), not just pass/fail, to drive near-miss UI and auto-repair.
  Keep binary satisfaction for convergence; expose graded for telemetry.
- **`evict_memo_for_obj` >> interactive incremental rebuild:** invalidate only downstream
  nodes whose input domain includes the changed entity; reuse cached B-rep subresults.
- **`Bound` extraction >> pre-solve feasibility:** Infinigen reads count/quantity limits
  out of the constraints *before* solving (`reasoning/constraint_bounding.py`). ncad analog:
  validate assembly cardinality / DOF-count feasibility (over-/under-constrained) up front,
  before invoking py-slvs.

---

## 3. Determinism: ncad's design is already stronger

**What Infinigen does.** Randomness is *live at build time*, so determinism is enforced by
discipline over global RNG state:

- **`FixedSeed`** (`util/math.py:17-52`): save / reseed / restore of exactly two global
  RNGs (Python `random`, numpy's legacy `np.random` singleton).
- **`int_hash` over MD5, not `hash()`** (`math.py:166-183`): Python's `hash()` is salted
  per process (`PYTHONHASHSEED`), so it differs across the separate coarse/populate/render
  processes; MD5 is unsalted and cross-process/machine-stable.
- **Position-stable sub-seeding** (`pipeline.py:31-100`): a stage body runs under
  `FixedSeed(int_hash((scene_seed, name)))`; the `*_chance` gate under
  `int_hash((scene_seed, name, 0))` (a different stream), so reordering or adding a stage
  never shifts a sibling's randomness.
- **Enforced seed-pinning** (`init.py:52-77`): running a non-coarse task without `--seed`
  *raises* ("results will not be view-consistent"), because each stage is a separate OS
  process that must re-derive the identical seed lattice.

**Known determinism holes (a checklist of what to avoid).**
- `FixedSeed` covers only those two RNGs. `np.random.default_rng()`/`Generator`, `secrets`,
  `uuid4`, and **Blender/Cycles C-side and GPU/CUDA randomness** are invisible to it >>
  silent nondeterminism.
- **`AddedSeed` is effectively broken** (`random.randbytes(n)`/`np.random.rand(n)` discard
  draws instead of reseeding); the real code uses `FixedSeed(int_hash(...))` everywhere.
- **`int_hash` tuple hashing has no separators**: `("ab","c")`, `("a","bc")`, `("abc",)`
  collide, and `12` (int) collides with `"12"` (str).

**Transfer to ncad (mostly confirmation that ncad's purity is stronger).**
- **ncad's purity dissolves the problem.** Infinigen re-derives its seed lattice in *every
  process* because randomness is live at build. ncad inverts this: all randomness is on the
  *authoring* side (a generator emits a fully-resolved document, §0), so the build is pure
  and needs **no seed at all**. What crosses the boundary is the document (content-addressed)
  + pinned kernel version. The entire cross-process RNG-divergence bug class does not exist.
- **Where the technique does transfer: ncad's generator layer.** A seeded generator should
  use exactly the `int_hash((generator_seed, node_path))` position-stable sub-seeding, so
  regenerating with an inserted/reordered node does not perturb siblings.
- **Two lessons for ncad's cache/hash (design §4a):**
  1. Never key a cache or seed on Python `hash()` or any per-process-nondeterministic
     source; use a fixed hash (SHA-256) over a canonical serialisation.
  2. Fix Infinigen's two hash weaknesses: add unambiguous field separators / length
     prefixes (so `("ab","c") != ("a","bc")`) and type-tag values (so `12 != "12"`) in the
     canonical subtree serialisation.
- **Enforce the pinning guard.** Mirror `parse_seed`'s raise: make it an error to run a
  build/cache step without its reproducibility inputs (document hash, kernel version), so
  divergence fails loud rather than producing silently inconsistent artifacts.
- **Audit that the pure executor draws zero randomness** ("third RNG not covered" is the
  canonical determinism-bug class; ncad's guarantee is that the build side never touches an
  RNG at all).

---

## Summary

| Idea | Verdict for ncad |
|------|------------------|
| Transpiler | Skip the visual round-trip (no GUI, §17); steal parametric-by-default fields, default-diff serialisation, DAG memoisation. |
| Constraint DSL | Adopt the deferred, `__bool__`-guarded, operator-overloaded **graph** as a backend-agnostic constraint representation feedable to py-slvs (exact) or a scorer (soft). |
| Exact vs. soft split | Keep mates/joints on the exact py-slvs path (DOF = null space); reserve annealing + graded violations + greedy staging strictly for optional *layout* features. |
| Incremental invalidation | `evict_memo_for_obj` is a blueprint for ncad's interactive incremental rebuild (§4). |
| Determinism | ncad's authoring-side randomness + pure build is strictly stronger than Infinigen's global-RNG save/restore; borrow only `int_hash`-by-path for the *generator*, and fix its separator/type-tag hash weaknesses in ncad's cache key (§4a). |

**Confidence:** medium-high on the mechanics (read directly from the Infinigen source with
file:line refs); the "transfer to ncad" column is architectural judgment against
`design.md`, not a validated decision. **Biggest open question:** whether ncad ever wants a
*soft* constraint/layout layer at all; if it does (auto-arrange, packing, generative
placement), the declarative-graph + feasibility-first-lexicographic pattern is the design to
adopt, kept strictly separate from the exact solver.
