"""Sample a declared point reference to its world position at each motion frame (in mm).

Shared by TraceExtractor and MeasureEvaluator: a point ref ({instance, point|connector}) names a
LOCAL point on a moving instance (mm) - either raw coords or a connector's local origin. This
resolves the local point, then applies the instance's per-frame placement to get the world point.

Units: a frame placement is a row-major world 4x4 whose ROTATION rows (0..2) are unit-free and whose
TRANSLATION row (3) is in METRES (AsmtTrajectoryMapper bakes it). The declared point is mm. So the
world point in mm is `point_mm . R + (t_metres / to_metres)`: the rotation is unit-free (applies to
mm directly), and the metres translation is converted back to the document unit. Returned in the
document unit (mm) so measures read mm/degrees directly; callers scale to metres for the viewer.
Module-level functions (no state); one public entry `sample_world_points`.
"""

from typing import Any

Vec3 = tuple[float, float, float]


def local_point(ref: dict, local_frames: dict) -> Vec3 | None:
    """The local point (mm) a ref names: raw ``point`` coords, or a connector's local origin.

    Returns None if the ref names a connector that is not in ``local_frames`` (unresolved).
    """
    if ref["point"] is not None:
        return ref["point"]
    frames = local_frames.get(ref["instance"]) or {}
    frame = frames.get(ref["connector"])
    if frame is None:
        return None
    origin = frame.origin
    return (float(origin[0]), float(origin[1]), float(origin[2]))


def apply_placement(point_mm: Vec3, placement: list, to_metres: float) -> Vec3:
    """World point in mm: ``point_mm . R`` (rotation unit-free) + the placement translation in mm.

    ``placement`` is a row-major 4x4 (rows 0..2 rotation, row 3 translation in metres). Row-vector
    convention: world[j] = sum_k point[k] * M[k][j] + M[3][j]. The translation row is metres, so it
    is divided by ``to_metres`` to return to the document unit (mm), matching the rotated mm point.
    """
    world = []
    for j in range(3):
        rotated = sum(point_mm[k] * placement[k][j] for k in range(3))
        world.append(rotated + placement[3][j] / to_metres)
    return (world[0], world[1], world[2])


def sample_world_points(ref: dict, frames: list[dict], local_frames: dict,
                        to_metres: float) -> list[Any]:
    """Per-frame world point (mm) for ``ref``; a frame missing the instance yields None for it.

    Returns one entry per frame: a (x, y, z) mm tuple, or None when the ref's instance is absent
    from that frame's placements or the connector is unresolved.
    """
    base = local_point(ref, local_frames)
    if base is None:
        return [None] * len(frames)
    out: list[Any] = []
    for frame in frames:
        placement = (frame.get("placements") or {}).get(ref["instance"])
        out.append(apply_placement(base, placement, to_metres) if placement is not None else None)
    return out
