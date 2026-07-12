import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_solver import MateSolver

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _prim(kind, a, b, value=None):
    return {"id": "s1", "kind": kind, "a": a, "b": b, "value": value,
            "a_ref": {"instance": "bolt", "connector": "c"},
            "b_ref": {"instance": "block", "connector": "c"}}


def test_valued_screw_advances_one_pitch_per_turn() -> None:
    # A bolt screwed into a block: connector Z along +Z at origin. One full turn (360 deg) with
    # pitch 4 advances the bolt 4mm along +Z. The two pins (angle + axial) are the screw lowering.
    bodies = {"block": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
              "bolt": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))}}
    seeds = {"block": [r[:] for r in _ID],
             "bolt": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 10, 1]]}
    prims = [_prim("axes_coincident", "A.axis", "B.axis"),
             _prim("dirs_angle", "A.secondary", "B.secondary", 360.0),
             _prim("point_plane_distance", "A.origin", "B.plane", 4.0)]
    outcome = MateSolver().solve(bodies, prims, ground_ids={"block"}, seeds=seeds)
    assert not outcome.failing_ids
    # The bolt origin sits 4mm along the axis from the block origin (magnitude; sign by convention).
    t = outcome.placements["bolt"][3]
    assert math.isclose(abs(t[2]), 4.0, abs_tol=1e-3)
    assert abs(t[0]) < 1e-3 and abs(t[1]) < 1e-3
