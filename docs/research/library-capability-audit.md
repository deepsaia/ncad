# Library capability audit: build123d + py-slvs vs ncad usage

A grounded audit (build123d 0.10.0, py-slvs 1.0.6, both what ncad ships on) of capabilities the
underlying libraries expose that ncad does NOT yet use, mapped to how NX / Creo / Fusion / Onshape
model the same thing and to the ncad phase each belongs in. Everything marked BUILDABLE below was
verified to run on the installed libraries (a quick spike, not just present in `dir()`).

The point: we are already paying for OCCT (via build123d/OCP) and SolveSpace (via py-slvs). Several
professional-grade features are a thin op/lowering layer over calls that already work, not new
kernel research. This doc is the shortlist; each item still gets its own brainstorm -> spec ->
plan when scheduled.

Method: enumerated `build123d` free functions + Shape/Solid/Face/Edge/Wire methods and the
`py_slvs.System.add*` surface, diffed against what `src/ncad` imports and calls (see the inventory
at the bottom), then spiked the high-value unused ones.

---

## A. Sketch solver (py-slvs) - constraints we do not expose yet

**Bucket 1.7 (DONE) shipped most of this section**: length_ratio, length_difference, equal_angle,
point_line_distance, points_horizontal/vertical, symmetric_h/v, and a solver-flexible 4-point cubic
bezier (`addCubic` + `addCubicLineTangent`). Those rows are removed below. What genuinely REMAINS:

| Missing constraint | py-slvs call (verified present) | NX/Creo/Fusion analogue | ncad phase |
|---|---|---|---|
| **same-orientation** (two curves/normals share orientation) | `addSameOrientation` | "Equal"/"Parallel" sense on curves | Phase 1 follow-up (niche) |
| **solver-flexible MULTI-SEGMENT / fit-point spline** | `addCubic` chaining + cross-segment G1/G2 | a fit-point spline whose many segments flex together | deferred (its own effort) |

**Parity note:** 1.7 made a SINGLE 4-control-point bezier flex in the solve (one `addCubic`
segment). A multi-point fit-point spline that flexes needs chaining several `addCubic` segments with
cross-segment tangent/curvature continuity; py-slvs has no fit-point primitive, so multi-point and
`interpolated` splines stay point-defined/pinned. That chaining is a separate, larger effort,
deferred. (`point-on-circle` is already covered by the existing `point_on` constraint.)

---

## B. Direct / dress-up ops - mostly SHIPPED (bucket 1.9)

Bucket 1.9 shipped the buildable Section-B items: **twisted extrude** (a `twist` on `extrude`),
**`max_fillet`** (largest-feasible-radius validator), and **primitive base bodies** (a `primitive`
op: box/cylinder/sphere/cone/torus/wedge). 2D sketch fillet/chamfer already shipped as sketch
`modify` ops. What REMAINS:

| Capability | build123d call | NX/Creo/Fusion analogue | disposition |
|---|---|---|---|
| **3D full-round fillet** ("Full Round Blend") | none (see below) | NX/Creo "Full Round Blend"; Fusion full-round fillet | DROPPED - not buildable on this stack |
| **tapered extrude (native)** | `Solid.extrude_taper` | draft-on-extrude | REDUNDANT - `extrude` already has `draft=` |
| **dprism (draft-prism pocket/pad)** | `Solid.dprism` | Creo "Sketched draft prism" | niche, deferred |

**Full-round-3D drop rationale:** build123d's `full_round` is a 2D SKETCH operation (it rounds a
profile end with a Voronoi-largest-circle arc and returns a Sketch), NOT the 3D "Full Round Blend"
(a variable ball rolling tangent between two side faces, consuming the middle face). OCCT's
`BRepFilletAPI` is edge-fillet only; there is no native full-round-blend, and synthesizing one
(remove the middle face + loft a tangent surface) is fragile/segfault-prone. A true full-round-blend
needs a commercial kernel or a from-scratch surface construction. Called out, not faked; revisit if
the kernel gains it.

---

## C. Surfacing / freeform (build123d Face) - Phase 9 foundation, verified present

ncad has no surface/sheet bodies yet (BodySet.kind reserves "surface"/"sheet"). build123d exposes
the full NX/Creo/Fusion surfacing kit over OCCT:

| Capability | build123d call | NX/Creo/Fusion analogue | ncad phase |
|---|---|---|---|
| **Boundary / patch surface** | `Face.make_surface`, `make_surface_patch` | NX "Through Curves/Curve Mesh"; Fusion "Patch/Loft surface" | Phase 9 |
| **Bezier / Gordon surface** | `Face.make_bezier_surface`, `make_gordon_surface` | NX freeform, Creo "Style" | Phase 9 |
| **Thicken a sheet into a solid** | `Solid.thicken` / `Face` thicken | "Thicken" (all) | Phase 9 |
| **Sew faces into a shell/solid** | `Face.sew_faces`, `Wire.stitch` | "Sew"/"Stitch" (all) | Phase 9/10 |
| **project curve onto a surface** | `Face.project_to_shape` (have for wrap) | "Project curve" | partly have |

This is a whole phase (9), noted here only to record that the library backs it.

---

## D. Drafting / documentation (build123d) - Phase 7, verified

| Capability | build123d call (spiked OK) | NX/Creo/Fusion analogue | ncad phase |
|---|---|---|---|
| **Hidden-line-removal projected views** | `Shape.project_to_viewport(eye)` -> (visible, hidden) edge sets | THE 2D drawing view generator (all) | Phase 7 |
| **SVG in/out** | `import_svg`, `export` to svg, `import_svg_as_buildline_code` | logo/profile import; drawing export | Phase 7 / Phase 1 profile import |
| **section view** | `section` free fn / `Solid.split` + keep | section views + "Section" feature | Phase 7 (have split) |

**NX/Creo/Fusion parity note:** `project_to_viewport` is exactly a drawing-view generator (returns
visible + hidden edges for an eye direction). Phase 7 (drafting) is built directly on it. SVG import
would also give Phase 1 a "trace a logo/outline into a sketch" path (Fusion "Insert SVG").

---

## E. Measurement / analysis (build123d Shape) - mostly SHIPPED (bucket 1.8)

Bucket 1.8 shipped the Measure kernel surface: `oriented_bounding_box`, `closest_points`, and
radius of gyration folded into `inertia` (plus scalar min-distance `distance`, already in 5.6).
Those rows are removed. What REMAINS:

| Capability | build123d call (spiked OK) | NX/Creo/Fusion analogue | ncad phase |
|---|---|---|---|
| **do_children_intersect** (fast self-clash) | `Compound.do_children_intersect` | interference quick-check | MOVED to the Phase 5 interference follow-up (overlaps InterferenceChecker) |

---

## F. Curve utilities (build123d Edge/Wire) - Phase 1/6 helpers, verified present

| Capability | build123d call | NX/Creo/Fusion analogue | ncad phase |
|---|---|---|---|
| **Distribute N frames along a curve** | `Edge.distribute_locations`, `locations` | "Point on curve by count"; pattern-along-curve seed | Phase 3 curve-pattern follow-up |
| **Tangent / normal / curvature at param** | `Edge.tangent_at`, `normal`, `curvature_comb` | curvature comb analysis | Phase 9 analysis |
| **Trim / split an edge at params** | `Edge.trim`, `trim_to_length` | sketch trim (have some) | Phase 1 follow-up |
| **Convex hull of points/wires** | `make_hull` / `Wire.make_convex_hull` | "Convex hull" (Fusion) | niche, Phase 9 |
| **spline approx through many points** | `Edge.make_spline_approx` | fit spline to point cloud | Phase 9 / reverse-eng |

---

## Recommended near-term picks (highest parity-per-effort)

The cheap, thin, one-op-each near-term picks are now SHIPPED: pick 1 sketch-constraint completeness
= bucket 1.7; the Measure mini-bucket = bucket 1.8; dress-up + base primitives (B) = bucket 1.9
(twisted extrude, max_fillet, `primitive` op; full-round-3D dropped, taper redundant). What remains
is phase-sized, not a thin near-term pick:

- **Surfacing (C) -> Phase 9** (`Face.make_surface`/`make_bezier_surface`/`thicken`/`sew`).
- **Drafting via HLR (D) -> Phase 7** (`Shape.project_to_viewport`; SVG import).
- **Solver-flexible multi-segment / fit-point splines (A) -> deferred** (`addCubic` chaining).
- **Sheet-metal brake-forming -> Phase 11** (`make_brake_formed`).
- **Curve utilities (F) -> Phase 1/3/9 helpers** (`distribute_locations`, `trim`, curvature).
- **`dprism` (B)** niche, deferred; **`do_children_intersect` (E)** -> Phase 5 interference follow-up.

The audit is now essentially drained of cheap wins; the next substantial capability work is a
phase-sized subsystem (surfacing / drafting), scheduled with its own brainstorm when picked up.

---

## Appendix: current usage inventory (for diffing later)

**build123d symbols ncad imports:** Axis, CenterOf, Color, Compound, Edge, Face, FontStyle,
GeomType, Helix, Keep, Location, Plane, Polygon, Pos, Rot, Solid, Text, Transition, Unit, Until,
Vector, Vertex, Wire, available_fonts, draft, export_gltf, export_step, export_stl, extrude,
import_step, loft, offset, sweep, trace.

**OCP modules ncad reaches into:** gp, GeomAbs, BRepAdaptor, XCAFDoc, XCAFApp, TopTools, TopoDS,
TopLoc, TopExp, TopAbs, TDocStd, TDataStd, TColStd, TCollection, TColgp, STEPCAFControl, Quantity,
Interface, GProp, Geom, BRepPrimAPI, BRepOffsetAPI, BRepGProp, BRepFilletAPI, BRepExtrema,
BRepBuilderAPI, BRepAlgoAPI, BRep.

**py-slvs `add*` ncad calls (~30 of ~50, after bucket 1.7):** addAngle, addArcLineTangent,
addArcOfCircle, addCircleV, addCubic, addCubicLineTangent, addCurvesTangent, addDiameter,
addDistanceV, addEqualAngle, addEqualLength, addEqualRadius, addLengthDifference, addLengthRatio,
addLineHorizontal, addLineSegment, addLineVertical, addMidPoint, addNormal2d, addNormal3dV,
addParallel, addParamV, addPerpendicular, addPoint2dV, addPoint3dV, addPointLineDistance,
addPointOnCircle, addPointOnLine, addPointsCoincident, addPointsDistance, addPointsHorizontal,
addPointsProjectDistance, addPointsVertical, addSymmetricHorizontal, addSymmetricLine,
addSymmetricVertical, addTransform, addWhereDragged, addWorkplane.

**py-slvs `add*` NOT yet used:** addConstraint(V), addDistance, addEntity,
addEqualLengthPointLineDistance, addEqualLineArcLength, addEqualPointLineDistance, addNormal3d,
addPointInPlane, addPointPlaneDistance, addSameOrientation, addSymmetric, addTranslate.
