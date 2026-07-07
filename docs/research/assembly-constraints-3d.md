# 3D assembly constraints: taxonomy, DoF diagnostics, solver split

Findings for ncad's Phase 5 (assemblies, design §7) and the DoF analysis of §8. This
grounds the *analysis/diagnostics* layer that sits on top of the numeric solver: what the
constraint vocabulary reduces to, how "over/under/exactly-constrained" is computed, and a
cheap combinatorial pre-check. The numeric solve itself is already decided (py-slvs, §8);
this note is about the layer that makes the result *legible*.

Primary source: **Haller, Lee-St. John, Sitharam, Streinu, White, "Body-and-cad geometric
constraint systems"** (2010, *Computational Geometry: Theory and Applications*; arXiv
1006.1126). The PDF is kept locally at
[`body-and-cad-geometric-constraint-systems-2010.pdf`](./body-and-cad-geometric-constraint-systems-2010.pdf)
(gitignored, not committed).

---

## The solver split (already in the design, restated for clarity)

ncad names two solvers, and it is easy to conflate them:

- **`py-slvs` (SolveSpace, GPL-3)** solves the *geometric / kinematic* constraint systems:
  2D sketches (Phase 1, done), **3D assembly mates (Phase 5)**, and kinematics (Phase 6).
  This is the solver for assembly constraints.
- **`OndselSolver`** solves *force-driven multibody dynamics* (Phase 14): gravity, forces,
  springs/dampers, simple contact. It enters only when the question is physics (a pendulum
  swinging), not mating.

So for 3D assembly constraints the solver is **py-slvs**. Ondsel is downstream and out of
scope until Phase 14. Both are GPL, consistent with the settled copyleft decision (§8, Q5).

## What ncad already plans (design §7, plan Phase 5)

Two declarative relationship families, both reducing to **named coordinate frames
(ports / mate connectors)** aligned frame-to-frame with an offset and a DoF signature (the
build123d / PartCAD / Onshape mate-connector model):

- **Assembly constraints:** mate/coincident, align, flush, offset, angle, tangent,
  parallel, perpendicular, concentric, symmetric, distance, width, lock.
- **Joints (DoF-bearing):** fixed, revolute, slider/prismatic, cylindrical, planar,
  ball, universal, screw, gear, rack-pinion, cam, belt, point-on-line/slot.

Phase 5 is **not started** and is gated behind Phase 4 (persistent naming, so a mate can
reference a face/axis that survives rebuilds).

---

## Finding 1: the constraint vocabulary reduces to 21 element-pair primitives

The paper enumerates the **complete set of 21 constraints** between geometric elements
(**point / line / plane**) on two rigid bodies, in three families (**coincidence,
distance, angular**):

| # | Constraint | # | Constraint | # | Constraint |
|---|---|---|---|---|---|
| 1 | point-point coincidence | 8 | line-line perpendicular | 15 | line-plane coincidence |
| 2 | point-point distance | 9 | line-line fixed-angular | 16 | line-plane distance |
| 3 | point-line coincidence | 10 | line-line coincidence | 17 | plane-plane parallel |
| 4 | point-line distance | 11 | line-line distance | 18 | plane-plane perpendicular |
| 5 | point-plane coincidence | 12 | line-plane parallel | 19 | plane-plane fixed-angular |
| 6 | point-plane distance | 13 | line-plane perpendicular | 20 | plane-plane coincidence |
| 7 | line-line parallel | 14 | line-plane fixed-angular | 21 | plane-plane distance |

**Takeaway for ncad.** This is a principled, complete normal form. ncad's §7 mate list is
a friendlier naming of these primitives (concentric = line-line coincidence of axes; flush
= plane-plane coincidence; angle = a fixed-angular; etc.). Designing the mate vocabulary to
*lower* to these 21 gives a small, closed, testable core rather than an open-ended list of
special cases, the same "vocabulary in one place" discipline the extrude/revolve/sweep
param helpers already follow.

## Finding 2: DoF = 6n - 6 - rank(rigidity matrix)

- Each body is a frame in **SE(3), 6 DoF**; an assembly of `n` bodies has `6n` DoF.
- Instantaneous motion is a **screw** `s = (-w, v)` (angular + translational); each
  constraint contributes rows to a **rigidity matrix** `R`.
- The structure is **infinitesimally rigid iff rank(R) = 6n - 6** (the `-6` is the global
  rigid-body freedom of the whole assembly).
- Therefore **free DoF = 6n - 6 - rank(R)**.

**Takeaway for ncad.** This is the design's "3D analogue of sketch DoF" (§8) made concrete:
over-/under-/exactly-constrained status is a rank computation on the constraint Jacobian,
which py-slvs already exposes. The value ncad adds is *interpreting* the number for the
user (and attributing redundant constraints by `id`, per the §10 validator discipline).
It is the same math as the Infinigen study's single-body `lstsq`-rank DoF trick
([[infinigen-transferable-ideas]]), generalized to the whole assembly.

A useful structural split the paper exposes: constraints separate into **angular** (they
constrain only the rotational `-w` half) and **blind** (translational). Angular constraints
are independently analyzable, which is why CAD solvers historically treat angle constraints
specially and is a real decomposition ncad can exploit for faster, clearer diagnostics.

## Finding 3: nested sparsity is a cheap *reject* screen (necessary, not sufficient)

A combinatorial pre-check on the constraint graph, before any numeric solve:

- A graph is **(k, l)-sparse** if every subset of `n'` vertices spans at most `k*n' - l`
  edges (tight if it spans exactly `k*n - l` total).
- Body-and-cad minimal rigidity implies **(6, 6, 3, 3)-nested tightness**: the whole
  constraint graph is (6, 6)-tight *and* its angular-only subgraph is (3, 3)-sparse.
- Checkable in polynomial time by **pebble-game** algorithms (paper §6).

**Critical caveat, proven in the paper with a counterexample:** nested sparsity is
**necessary but NOT sufficient** for rigidity. So it can cheaply *reject* a grossly
over-constrained assembly ("this cannot be well-constrained") but cannot *confirm* one is
well-constrained. Treat it as a fast, deterministic pre-filter that emits an id-tagged
diagnostic, not as the answer; the numeric rank computation (Finding 2) remains the
authority.

---

## Net recommendation for Phase 5

1. **Lower every mate/joint to the 21-primitive normal form** as the internal
   representation; the user-facing vocabulary is sugar over it.
2. **Report DoF = 6n - 6 - rank** as the assembly's constraint status, with redundant
   constraints attributed by `id` (the 3D counterpart of the sketch-status work in
   bucket 1.5).
3. **Optionally run the nested-sparsity pebble-game as a pre-solve screen** to reject
   over-constrained inputs fast and cheaply; never rely on it as a sufficiency proof.
4. Keep py-slvs as the numeric solver; this is all the *diagnostics* layer on top, the
   "better than a bare solver" value, exactly parallel to the "better than bare OCCT"
   robustness framing for the kernel.

**Confidence:** high on the taxonomy, the `6n - 6` rank criterion, and the
necessary-not-sufficient status of nested sparsity (all quoted from the paper). Medium on
the *engineering* payoff of the pebble-game screen at ncad's assembly sizes, unmeasured.
**Biggest open question:** whether py-slvs's own DoF/redundancy reporting is already rich
enough that ncad only needs to *surface and attribute* it, or whether the rigidity-matrix
analysis is worth reimplementing for better diagnostics, a call to make when Phase 5 starts,
not before.
