import math

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_solver import MateSolver, _seed_pose

_ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _rot_z(deg):
    # row-major row-vector: row i is the image of basis e_i (BodyPose convention).
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _prim(mate_id, kind, ai, ac, bi=None, bc=None, a="A.axis", b="B.axis", value=None):
    return {"id": mate_id, "kind": kind, "a": a, "b": b, "value": value,
            "a_ref": {"instance": ai, "connector": ac},
            "b_ref": None if bi is None else {"instance": bi, "connector": bc}}


def test_concentric_plus_coincident_lands_moving_on_ground() -> None:
    # Ground body A: connector "hole" at (10, 2, 0), axis +Z. Moving body B: connector "pin" at its
    # own origin, axis +Z. concentric + coincident must move B so pin coincides with hole.
    bodies = {
        "base": {"hole": ConnectorFrame.from_planar((10, 2, 0), (0, 0, 1))},
        "arm": {"pin": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
    }
    prims = [
        _prim("m1", "axes_coincident", "arm", "pin", "base", "hole"),
        _prim("m2", "points_coincident", "arm", "pin", "base", "hole", a="A.origin", b="B.origin"),
        _prim("m2", "anti_parallel_dirs", "arm", "pin", "base", "hole"),
    ]
    seeds = {"base": [r[:] for r in _ID],
             "arm": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [50, -9, 3, 1]]}
    outcome = MateSolver().solve(bodies, prims, ground_ids={"base"}, seeds=seeds)
    assert outcome.status in ("solved", "under_constrained")
    assert not outcome.failing_ids
    # arm's solved translation lands its pin origin (0,0,0 local) onto the hole at (10,2,0).
    t = outcome.placements["arm"][3]
    assert math.isclose(t[0], 10.0, abs_tol=1e-4)
    assert math.isclose(t[1], 2.0, abs_tol=1e-4)
    assert math.isclose(t[2], 0.0, abs_tol=1e-4)


def test_ground_body_keeps_its_seed() -> None:
    bodies = {"base": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))}}
    seeds = {"base": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [7, 8, 9, 1]]}
    outcome = MateSolver().solve(bodies, [], ground_ids={"base"}, seeds=seeds)
    assert outcome.placements["base"][3][:3] == [7, 8, 9]


def test_deterministic_same_input_same_matrices() -> None:
    bodies = {
        "base": {"hole": ConnectorFrame.from_planar((10, 2, 0), (0, 0, 1))},
        "arm": {"pin": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))},
    }
    prims = [_prim("m2", "points_coincident", "arm", "pin", "base", "hole",
                   a="A.origin", b="B.origin")]
    seeds = {"base": [r[:] for r in _ID],
             "arm": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [5, 5, 5, 1]]}
    first = MateSolver().solve(bodies, prims, ground_ids={"base"}, seeds=seeds)
    second = MateSolver().solve(bodies, prims, ground_ids={"base"}, seeds=seeds)
    assert first.placements["arm"] == second.placements["arm"]


def test_seed_pose_identity_when_no_seed():
    tx, ty, tz, quat = _seed_pose(None)
    assert (tx, ty, tz) == (0.0, 0.0, 0.0)
    assert quat == (1.0, 0.0, 0.0, 0.0)


def test_seed_pose_extracts_translation():
    _, _, _, quat = _seed_pose([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [4, 5, 6, 1]])
    tx, ty, tz, _q = _seed_pose([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [4, 5, 6, 1]])
    assert (tx, ty, tz) == (4.0, 5.0, 6.0)
    assert quat == (1.0, 0.0, 0.0, 0.0)   # identity rotation -> identity quat


def test_seed_pose_seeds_authored_rotation_as_quaternion():
    # a 90 deg rotation about Z must seed a non-identity quaternion (qw=cos45, qz=sin45)
    _, _, _, (qw, qx, qy, qz) = _seed_pose(_rot_z(90))
    assert math.isclose(qw, math.cos(math.radians(45)), abs_tol=1e-9)
    assert math.isclose(qz, math.sin(math.radians(45)), abs_tol=1e-9)
    assert math.isclose(qx, 0.0, abs_tol=1e-9) and math.isclose(qy, 0.0, abs_tol=1e-9)


def test_seed_pose_quaternion_is_normalized():
    for deg in (30, 90, 180, 270):
        _, _, _, q = _seed_pose(_rot_z(deg))
        assert math.isclose(sum(c * c for c in q), 1.0, abs_tol=1e-9)


def test_rotated_ground_body_reads_back_its_rotation():
    # a grounded body seeded at 90 deg about Z keeps that orientation (it never moves).
    bodies = {"base": {"c": ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))}}
    seeds = {"base": _rot_z(90)}
    outcome = MateSolver().solve(bodies, [], ground_ids={"base"}, seeds=seeds)
    pose = outcome.placements["base"]
    # row 0 (image of e_x) should be ~(0, 1, 0) for a +90 deg Z rotation
    assert math.isclose(pose[0][0], 0.0, abs_tol=1e-6)
    assert math.isclose(pose[0][1], 1.0, abs_tol=1e-6)
