from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_solver import MateSolver

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _prim(mate_id, kind, ai, ac, bi, bc, a="A.origin", b="B.origin"):
    return {"id": mate_id, "kind": kind, "a": a, "b": b, "value": None,
            "a_ref": {"instance": ai, "connector": ac},
            "b_ref": {"instance": bi, "connector": bc}}


def test_duplicate_constraint_is_redundant_not_failing() -> None:
    # Two identical points_coincident primitives under different mate ids: the second is redundant.
    bodies = {
        "base": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
        "arm": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
    }
    prims = [
        _prim("m1", "points_coincident", "arm", "c", "base", "c"),
        _prim("m2", "points_coincident", "arm", "c", "base", "c"),
    ]
    seeds = {"base": [r[:] for r in _ID],
             "arm": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [5, 5, 5, 1]]}
    outcome = MateSolver().solve(bodies, prims, ground_ids={"base"}, seeds=seeds)
    # py-slvs reports code 5 (redundant-but-consistent) and populates the redundant split.
    assert outcome.solve_code == 5
    assert not outcome.failing_ids
    # At least one of the duplicated mate ids is flagged redundant (py-slvs may flag both).
    assert set(outcome.redundant_ids) & {"m1", "m2"}
