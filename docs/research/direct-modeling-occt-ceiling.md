# Research: OCCT direct/synchronous-modeling robustness ceiling

*Question:* how far can history-free face editing go on OCCT before it needs a
dedicated approach? *Decision recorded in* `design.md` §3, §19.

## What the OCCT APIs give (and don't)

History-free face editing on OCCT is **feasible but narrow**:

- **delete_face / defeature** >> `BRepAlgoAPI_Defeaturing` (wraps
  `BOPAlgo_RemoveFeatures`); solids only; fills the gap by extending adjacent faces
  and re-intersecting. The most useful native "direct" op.
- **offset_face / thicken** >> `BRepOffsetAPI_MakeOffsetShape` / `MakeThickSolid`;
  whole-shape single offset (not per-face); only `Skin` mode implemented;
  `Intersection` mode and self-intersection elimination **not implemented**.
- **local features** >> `BRepFeat_MakePrism/DPrism/Revol/Gluer` *add/remove* matter
  tied to a face; they do **not** move/replace a face.
- **move_face / replace_face** >> *no dedicated API*; synthesize via rebuild +
  `BRepAlgoAPI_Cut`/`Fuse` + heal. Boolean History tracks faces/edges, not vertices.
- **healing** >> `ShapeFix_Shape`, `ShapeUpgrade_UnifySameDomain`; capped by
  `MaxTolerance`; does not resolve self-intersections.

## Where it breaks (tracker-verified)

- Defeaturing **hangs indefinitely** on a small face (OCCT #33561); **corrupts
  topology beyond the removed region** (#33693); throws on multi-group removal
  (#33707); over-unifies unrelated faces (#30318). Documented to fail on **tangent
  adjacent faces** and when extended faces don't cover the feature.
- Offset/shell fails `BRep_API: command not done` on thin walls / intricate
  contours, **direction-sensitive** (−0.5 works, +0.5 fails; maintainer-tagged
  "OCC kernel issue"), CadQuery #1494/#1515/#1476/#1768. Fails on C0 BSplines,
  >3 edges at a vertex, offset > smallest concave radius.
- Fillets/blends fail order-dependently, can produce malformed-but-"valid" solids
  (build123d #1224, FreeCAD #29480, pythonocc #1281).
- Booleans under-fuse rotated copies (OCCT #1041); `UnifySameDomain` injects
  self-intersections (#1193); **`BRepCheck_Analyzer` sometimes reports invalid
  geometry as valid (#1315)**: a validity gate is necessary but not fully trusted.

## The real gap: move a face vs. maintain relationships

Moving a face on well-behaved topology is doable. Auto-inferring and **maintaining**
relationships (Siemens Synchronous Technology / "Live Rules") is a different class:
an application layer on **Parasolid + D-Cubed DCM** with a decision engine: a
commercial kernel plus a separate constraint solver. The underpinnings (geometric
constraint solving + persistent naming) are open research; FreeCAD's
topological-naming problem is the standing proof. OCCT ships neither a constraint
solver nor stable persistent IDs. Realistically multi-year, PhD-grade.

Every mature direct/synchronous modeler uses a commercial kernel + solver, **not
OCCT** (Solid Edge/NX: Parasolid+D-Cubed; SpaceClaim/Fusion: ACIS; SolidWorks:
Parasolid; CATIA: CGM). No OCCT-based project implements true ST-style maintenance.

## Recommendation (adopted)

**v1 direct-modeling scope on OCCT:**
1. `delete_face`/defeature on solids, **non-tangent adjacent faces only**: detect
   tangency and refuse.
2. `offset_face`/thicken: planar/analytic faces, single offset, < smallest local
   concave radius; reject C0 BSpline surfaces.
3. `move_face`/`replace_face`: planar faces on well-behaved topology via
   rebuild + boolean + `UnifySameDomain` + `ShapeFix`.

Gate every op with `BRepCheck_Analyzer` **plus** an independent volume/area/
closedness check.

**Excluded from v1:** auto relationship inference/maintenance (Live-Rules), moving
faces in fillet/blend/tangent chains, per-face variable offset, self-intersecting
offsets, persistent-naming guarantees across edits.

**Spike (2–4 wks, Phase 4; previewed bucket 0.5):** on a representative dirty import,
run Defeaturing + planar move_face + heal; measure validity-gate pass rate,
tangent-failure rate, hang/timeout incidence. This defines the achievable envelope.

**Confidence:** high on APIs/limits/market pattern (OCCT docs + ~20 reproducible
tracker/GitHub issues). **Biggest unknown:** empirical success rate of the
well-behaved subset on ncad's own real geometry. The spike closes it.

## Bucket 4.4 spike verdicts (2026-07-14)

- **`replace_face`: DROPPED (genuinely undoable on our stack).** A face swap needs a custom
  `BRepTools_Modification` subclass fed to `BRepTools_Modifier`, but OCP does not expose a Python
  constructor for `BRepTools_Modification` (`TypeError: No constructor defined`), and the only
  concrete subclasses (`Trsf`/`GTrsf`/`NurbsConvert`/`Copy` modifications) apply transforms, not a
  new surface. There is no rebuild-and-boolean synthesis for an arbitrary face swap either. Called
  out and not built (never faked); revisit if a commercial kernel or a py-OCCT modification hook
  lands.
- **`reposition_hole`: BUILT.** A history-free "move hole": read the hole's cylindrical face
  (axis/radius/location), FILL it by fusing a plug cylinder spanning the solid along the axis, then
  RE-CUT an identical cylinder at the target. Purely additive booleans, robust on the validity
  gate. See `src/ncad/ops/reposition_hole_op.py`.
