"""Attempt a planar move_face, synthesized via fuse + heal (OCCT has no native move-face API)."""

from typing import Any

from build123d import Solid, import_step

from spikes.direct_modeling_4_0.probes.oracle import evaluate


def move_face_probe(step_path: str, face_index: int, delta: float) -> dict[str, Any]:
    """Push planar face ``face_index`` outward by ``delta`` along its normal; oracle verdict dict.

    OCCT has no move-face API. This synthesizes the effect: extrude the target face by ``delta``
    along its normal into a slab and fuse it onto the solid, then heal (ShapeFix). The oracle
    then judges the result across all three tiers; a fuse that BRepCheck calls valid but that is
    actually empty/degenerate surfaces as a gate-vs-reality disagreement (the #1315 signal).
    Any hard failure raises, which GuardedRunner records as "raised".
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse  # pyrefly: ignore[import-error]
    from OCP.ShapeFix import ShapeFix_Shape  # pyrefly: ignore[import-error]

    before = import_step(step_path)
    solid = before.solids()[0]
    faces = solid.faces()
    if face_index >= len(faces):
        return {"skipped": True, "reason": "face_index out of range"}
    face = faces[face_index]

    # Build a slab from the face profile extruded delta along its normal, fuse it on, then heal.
    normal = face.normal_at(face.center())
    slab = Solid.extrude(face, normal * delta)
    fuse = BRepAlgoAPI_Fuse(solid.wrapped, slab.wrapped)
    fuse.Build()
    fix = ShapeFix_Shape(fuse.Shape())
    fix.Perform()
    after = Solid(fix.Shape())

    result = evaluate(solid, after, "move_face")
    result["delta"] = delta
    result["fuse_done"] = bool(fuse.IsDone())
    return result
