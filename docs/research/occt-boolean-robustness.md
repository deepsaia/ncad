# Research: solving OCCT boolean/fillet fragility

*Question:* can ncad fix OCCT's boolean-operation (BOP) and fillet robustness
fragility, by upstreaming to OCCT or by owning a layer on top? *Decision recorded
in* `design.md` §4, §19.

**Verdict:** build a **robustness layer we own** on top of OCCT; **do not** rely on
upstreaming core fixes. Confidence: high.

## Root cause: fundamental substrate, fixable instances

OCCT's own docs attribute BOP failure to "self-interfered arguments, inappropriate
or ungrounded values of the argument tolerances." "Interference" is *defined* by
tolerance overlap, so **tolerance mismatch/inflation is the mechanistic centre** of
most failures. Concrete failure classes: sliver faces bound by very short edges,
self-intersections that corrupt the whole model, and near-coincident geometry (a
rotation introducing ~1e-14 error turns coincident vertices into merely
near-coincident ones). The float + tolerance BRep design makes some inconsistency
inherent, but individual failures are largely addressable via input conditioning and
tolerance tuning, which is exactly why OCCT ships fuzzy, gluing, and healing.

**Improving?** Yes, modestly, in maintenance lines. 7.9.0 (2025-02) claims "improved
robustness of boolean operations"; 7.9.3 (2025-12) bundles BOP + fillet crash/hang
fixes. 8.0.0 (2026-05) is an architecture/C++17 release; its only BOP change is
thread-safety, not accuracy. The deep algorithmic rework (BVH, per-curve tolerances)
predates this window (7.2-7.4).

## Path A (upstream to OCCT): impractical for ncad

Procedurally open, practically gated:
- Contribution is GitHub PRs to `Open-Cascade-SAS/OCCT`, but requires a
  **wet-signature CLA assigning *joint copyright* to Open Cascade SAS** (French law,
  print/sign/scan), bot-enforced.
- Merge authority is highly centralized (one maintainer authored ~80% of recent
  merges). For **core BOP/fillet**, staff land fixes while comparable external PRs
  stall for months or are closed on CLA grounds.
- **Version-lock tax:** OCCT ships ~every 14 months, and OCP/cadquery-ocp lags major
  releases (8.0.0 had no stable OCP binding weeks after release). A landed fix would
  not reach ncad's Python stack for ~a year.

File targeted **bug reports** upstream, but do not put robustness on that timeline.

## Path B (own a layer): tractable, battle-tested

Every major OCCT-based product builds this from documented OCCT APIs. ncad's kernel
adapter runs a four-step ladder inside each fragile op, invisible to the document
and fitting the uniform pure op signature (retry/validation already thread through):

1. **Normalize + gate inputs:** `BRepCheck_Analyzer`, then
   `ShapeFix_ShapeTolerance.LimitTolerance` (optional `BRepBuilderAPI_Sewing`) so
   operand tolerances are sane before the op.
2. **Fuzzy retry ladder:** `SetNonDestructive(true)` + escalating `SetFuzzyValue`,
   auto-tuned to model scale (`sqrt(bbox.SquareExtent()) * Precision::Confusion()`,
   FreeCAD's heuristic); try a plain op first, stop at the first valid result.
3. **Post-op cleanup:** `ShapeUpgrade_UnifySameDomain` to merge coplanar
   faces/collinear edges (CadQuery runs this by default after every boolean).
4. **Validate + heal-and-retry:** re-check `BRepCheck_Analyzer.IsValid()`; on
   invalid, `ShapeFix_Shape` and retry, else fail loudly by `id`.

**Prior art:** CadQuery auto-`.clean()`s (`UnifySameDomain`) after cut/union/
intersect and exposes fuzzy `tol=` on all three; build123d exposes fuzzy on `fuse`
only (an asymmetry ncad closes). FreeCAD ships "auto-refine after boolean," a Check
Geometry tool (`BRepCheck_Analyzer` + `BOPAlgo_ArgumentAnalyzer`), and fuzzy
`Tolerance` properties; UKAEA's `overlap_checker`/`fast_ctd` implement the
retry-with-increasing-fuzzy loop in production.

## Biggest unknown

How well one auto-tuned fuzzy value generalizes across ncad's geometry (multi-storey
walls, roofs, balcony junctions) vs. needing per-op tuning. Fuzzy has real downsides
(it can *cause* failures a plain boolean avoids, and needs vertex re-snapping), so
the ladder tries a plain op first. Settle empirically with a golden-geometry
regression suite over the example briefs (design §19).
