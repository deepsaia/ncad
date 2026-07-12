import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_solver import MateSolver

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _prim(mate_id, kind, ai, ac, bi=None, bc=None, a="A.axis", b="B.axis", value=None):
    return {"id": mate_id, "kind": kind, "a": a, "b": b, "value": value,
            "a_ref": {"instance": ai, "connector": ac},
            "b_ref": None if bi is None else {"instance": bi, "connector": bc}}


def test_distance_holds_gap_along_target_normal() -> None:
    # Ground plate top at z=0 (normal +Z). Moving peg base connector; distance 5 => peg origin
    # sits 5 above the plate along +Z.
    bodies = {
        "plate": {"top": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
        "peg": {"base": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
    }
    prims = [_prim("m1", "point_plane_distance", "peg", "base", "plate", "top",
                   a="A.origin", b="B.plane", value=5.0)]
    seeds = {"plate": [r[:] for r in _ID],
             "peg": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 20, 1]]}
    outcome = MateSolver().solve(bodies, prims, ground_ids={"plate"}, seeds=seeds)
    assert not outcome.failing_ids
    assert math.isclose(abs(outcome.placements["peg"][3][2]), 5.0, abs_tol=1e-3)


def test_lock_pins_the_body_to_its_seed() -> None:
    bodies = {"a": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))}}
    prims = [_prim("m1", "lock", "a", "c", a="A", b=None)]
    seeds = {"a": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [3, 4, 5, 1]]}
    outcome = MateSolver().solve(bodies, prims, ground_ids=set(), seeds=seeds)
    assert outcome.placements["a"][3][:3] == [3, 4, 5]
