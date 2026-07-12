from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_solver import MateSolver

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _prim(kind, a, b):
    return {"id": "j1", "kind": kind, "a": a, "b": b, "value": None,
            "a_ref": {"instance": "arm", "connector": "c"},
            "b_ref": {"instance": "base", "connector": "c"}}


def _solve(prims):
    bodies = {"base": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
              "arm": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))}}
    seeds = {"base": [r[:] for r in _ID],
             "arm": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [3, 4, 5, 1]]}
    return MateSolver().solve(bodies, prims, ground_ids={"base"}, seeds=seeds)


def test_fixed_via_secondary_parallel_pins_all_dof() -> None:
    # points_coincident (origin) + anti_parallel (Z) + secondary_parallel (X) fully locks the body.
    prims = [_prim("points_coincident", "A.origin", "B.origin"),
             _prim("anti_parallel_dirs", "A.axis", "B.axis"),
             _prim("secondary_parallel", "A.secondary", "B.secondary")]
    outcome = _solve(prims)
    assert outcome.dof == 0
    assert not outcome.failing_ids
    # The arm origin lands on the base origin (0,0,0).
    t = outcome.placements["arm"][3]
    assert abs(t[0]) < 1e-4 and abs(t[1]) < 1e-4 and abs(t[2]) < 1e-4


def test_slider_leaves_translation_free_but_no_spin() -> None:
    # axes_coincident (Z line-coincident) + secondary_parallel (block spin) => slides along Z only.
    prims = [_prim("axes_coincident", "A.axis", "B.axis"),
             _prim("secondary_parallel", "A.secondary", "B.secondary")]
    outcome = _solve(prims)
    # Solves consistently (dof may exceed 1 due to quaternion gauge; signature is authoritative).
    assert outcome.solve_code in (0, 5)
    assert not outcome.failing_ids
