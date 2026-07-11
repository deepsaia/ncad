"""Attempt BRepAlgoAPI_Defeaturing (remove one face) on an imported STEP solid."""

from typing import Any

from build123d import Solid, import_step

from spikes.direct_modeling_4_0.probes.oracle import evaluate


def defeature_probe(step_path: str, face_index: int) -> dict[str, Any]:
    """Remove face ``face_index`` from the STEP solid; return the oracle verdict dict.

    Imports inside the child (no shape crosses the process boundary). Any OCP failure raises,
    which GuardedRunner records as "raised"; a hang/segfault is recorded as timeout/crashed.
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Defeaturing  # pyrefly: ignore[import-error]
    from OCP.TopTools import TopTools_ListOfShape  # pyrefly: ignore[import-error]

    before = import_step(step_path)
    solid = before.solids()[0]
    faces = solid.faces()
    if face_index >= len(faces):
        # No such face on this input: report a skip so the driver does not count it as a run.
        return {"skipped": True, "reason": "face_index out of range"}
    target = faces[face_index]

    remove = TopTools_ListOfShape()
    remove.Append(target.wrapped)
    defeat = BRepAlgoAPI_Defeaturing()
    defeat.SetShape(solid.wrapped)
    defeat.AddFacesToRemove(remove)
    defeat.Build()
    after = Solid(defeat.Shape())

    result = evaluate(solid, after, "defeature")
    result["done"] = bool(defeat.IsDone())
    return result
