"""Attempt a whole-solid offset/thicken (BRepOffsetAPI) on an imported STEP solid."""

from typing import Any

from build123d import import_step

from spikes.direct_modeling_4_0.probes.oracle import evaluate


def offset_probe(step_path: str, distance: float) -> dict[str, Any]:
    """Offset the whole solid by ``distance`` (thicken/thin); return the oracle verdict dict.

    Uses build123d's offset_3d (BRepOffsetAPI_MakeThickSolid under the hood). A negative
    distance thins, a positive distance grows. Direction sensitivity is a documented failure
    mode, so the driver runs this probe in both directions. Any failure raises (recorded by
    GuardedRunner); a hang is recorded as timeout.
    """
    before = import_step(step_path)
    solid = before.solids()[0]
    # offset_3d(openings, thickness): no openings (closed offset), positional thickness.
    after = solid.offset_3d(None, distance)

    result = evaluate(solid, after, "offset")
    result["distance"] = distance
    return result
