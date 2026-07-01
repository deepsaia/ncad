# Research — Class A surfacing feasibility on OCCT

*Question:* can OCCT reach genuine Class A (G2–G3, reflection quality), or is it a
specialist kernel / out of scope? *Decision recorded in* `design.md` §6, §19.

**Bottom line:** feasible-but-limited for engineering/G2 surfacing; **true Class A
is out of scope on OCCT alone.** Confidence: high.

## What OCCT constructs and analyzes

- **Continuity ceiling is G2.** `BRepOffsetAPI_MakeFilling` accepts only
  `GeomAbs_C0`/`G1`/`G2` — **no G3 constraint exists**. `ThruSections` continuity
  via `SetContinuity`; `GeomFill_ConstrainedFilling` documents only G1/tangency.
  B-spline surfaces allow degree up to 25 (high parametric continuity representable).
- **Curvature analysis is native.** `GeomLProp_SLProps` / `BRepLProp_SLProps` give
  Gaussian/mean/principal curvature, directions, normals; gap/deviation via
  `BRepExtrema_DistShapeShape`.
- **No native styling-quality analysis.** OCCT master has **0 hits for "Zebra" /
  "Isophote"** — must be hand-built on curvature/normal primitives.
  `HLRAppli_ReflectLines` yields view-dependent silhouettes, not zebra.
- **No general surface fairing.** `FairCurve_*` is 2D-curve-only; the only
  variational surface tool is `GeomPlate` (thin-plate, G0/G1-ish).

## What Class A requires (and why it's specialized)

Class A is not standardized; convention is **G2 mandatory floor, G3 for "perfect"
reflections** (Autodesk Alias). The specialization is the *workflow*: minimal
single-span low-degree (~degree-5) patches, manual control-point sculpting,
interactive diagnostics (Alias continuity locator; ICEM Surf real-time
reflection/curvature/deviation "to within a micron"). G1 suffices for ordinary
mechanical parts; G2 is the reflective-surface threshold.

## Quality ceiling — evidence

An OCCT contributor: "the surfacing API of OpenCASCADE is limited"; its
`Plate`/variational filling is "unlikely to be class A." Robustness is
documented-shaky: fillet/offset/boolean are "check `IsDone()` and hope," offsets
warn self-intersection removal "is not yet implemented," and boolean tolerances
**monotonically accumulate**. Even Rhino is judged "not on par with Alias."

## Specialist landscape

OSS NURBS reps (OpenNURBS, tinynurbs, SISL[AGPL], Geometric Tools) do evaluation,
**none advertise Class-A tooling**. OSS fairing is mesh-based (CGAL `fair()`,
libigl), not NURBS. Class A is effectively commercial (Alias, ICEM Surf, CATIA);
embeddable kernels (Parasolid, ACIS, C3D — the last markets a "FairCurveModeler")
do free-form surfacing but aren't drop-in Class A. Rhino is the affordable ceiling.

## Recommendation (adopted)

Ship the **G2 engineering-surfacing subset**; keep true Class A out of scope
(aspirational at most).

Reachable on OCCT: G0/G1/G2 fills/blends (`MakeFilling`), lofts (`ThruSections` +
`SetContinuity`), `GeomFill`/`GeomPlate` patches; and **curvature/deviation/zebra
analysis we build ourselves** on `GeomLProp_SLProps` + `BRepExtrema_DistShapeShape`.

**Phase 9 v1 surfacing gate:**
1. Construct G2-continuous multi-patch fills/lofts; validator asserts achieved
   continuity via `BRepLProp::Continuity` at seams (fail if below requested order).
2. Curvature pass: sample principal/Gaussian/mean; emit curvature-comb + deviation
   report as structured `Issue`s.
3. A zebra/isophote *analysis* overlay (read-only), not a fairing optimizer.
4. Documented non-goals: no G3, no interactive control-point sculpting, no
   automatic curvature fairing, no reflection-fairness optimization.

**Confidence:** high on the G2 ceiling, missing zebra/fairing, "Class A =
specialist workflow." **Biggest unknown:** how *robust* OCCT's G2 fills/blends are
on non-trivial real geometry — a surfacing spike settles it. Secondary: whether a
licensable module (C3D FairCurveModeler) could later lift G3 without a kernel swap.
