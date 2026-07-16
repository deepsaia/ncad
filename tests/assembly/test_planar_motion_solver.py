import math

import pytest

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mechanism_plane import MechanismPlane
from ncad.assembly.planar_motion_solver import PlanarMotionSolver

pytestmark = pytest.mark.slow

_R, _L = 20.0, 70.0


def _crank_slider():
    # world-frame connector frames (Z = the mechanism normal = +Z here).
    def axis(x, y):
        return ConnectorFrame.from_axis((x, y, 0.0), (0, 0, 1))

    frames = {
        "ground": {"pivot": axis(0, 0), "way0": axis(0, 0), "way1": axis(0, 10)},
        "crank": {"hub": axis(0, 0), "pin": axis(_R, 0)},
        "rod": {"big": axis(_R, 0), "small": axis(0, math.sqrt(_L ** 2 - _R ** 2))},
        "piston": {"wrist": axis(0, math.sqrt(_L ** 2 - _R ** 2)),
                   "s0": axis(0, 0), "s1": axis(0, 10)},
    }
    joints = [
        {"id": "drive", "type": "revolute",
         "a": {"instance": "ground", "connector": "pivot"},
         "b": {"instance": "crank", "connector": "hub"}},
        {"id": "crankPin", "type": "revolute",
         "a": {"instance": "crank", "connector": "pin"},
         "b": {"instance": "rod", "connector": "big"}},
        {"id": "wristPin", "type": "revolute",
         "a": {"instance": "rod", "connector": "small"},
         "b": {"instance": "piston", "connector": "wrist"}},
        {"id": "slide", "type": "slider",
         "a": {"instance": "ground", "connector": "way0"},
         "b": {"instance": "piston", "connector": "s0"}},
    ]
    return frames, joints


def test_crank_slider_matches_analytic_stroke():
    frames, joints = _crank_slider()
    plane = MechanismPlane.from_axis_point((0, 0, 0), (0, 0, 1))
    values = [k * 30.0 for k in range(13)]
    driver = {"joint": "drive", "pivot": {"instance": "ground", "connector": "pivot"},
              "moving": {"instance": "crank", "connector": "pin"}}
    poses = PlanarMotionSolver().solve(frames, joints, {"ground"}, plane, driver, values)
    assert len(poses) == len(values)
    for theta, pose in zip(values, poses):
        # piston wrist world y = analytic stroke. Apply the pose delta to the rest wrist point.
        m = pose["piston"]
        wrist_rest = (0.0, math.sqrt(_L ** 2 - _R ** 2), 0.0)
        y = sum(wrist_rest[k] * m[k][1] for k in range(3)) + m[3][1]
        cpx = _R * math.cos(math.radians(theta))
        analytic = _R * math.sin(math.radians(theta)) + math.sqrt(_L ** 2 - cpx ** 2)
        assert math.isclose(y, analytic, abs_tol=0.5)


_A, _B, _C, _D = 25.0, 60.0, 45.0, 55.0  # a crank-rocker four-bar (Grashof)


def _four_bar():
    def axis(x, y):
        return ConnectorFrame.from_axis((x, y, 0.0), (0, 0, 1))

    frames = {
        "ground": {"o2": axis(0, 0), "o4": axis(_D, 0)},
        "input": {"j2": axis(0, 0), "ja": axis(_A, 0)},
        "coupler": {"ja": axis(_A, 0), "jb": axis(_D, _C)},  # rough closed rest pose
        "rocker": {"o4": axis(_D, 0), "jb": axis(_D, _C)},
    }
    joints = [
        {"id": "drive", "type": "revolute",
         "a": {"instance": "ground", "connector": "o2"},
         "b": {"instance": "input", "connector": "j2"}},
        {"id": "ja", "type": "revolute",
         "a": {"instance": "input", "connector": "ja"},
         "b": {"instance": "coupler", "connector": "ja"}},
        {"id": "jb", "type": "revolute",
         "a": {"instance": "coupler", "connector": "jb"},
         "b": {"instance": "rocker", "connector": "jb"}},
        {"id": "o4", "type": "revolute",
         "a": {"instance": "ground", "connector": "o4"},
         "b": {"instance": "rocker", "connector": "o4"}},
    ]
    return frames, joints


def test_four_bar_closed_loop_converges_and_rocker_sweeps():
    frames, joints = _four_bar()
    plane = MechanismPlane.from_axis_point((0, 0, 0), (0, 0, 1))
    values = [k * 10.0 for k in range(37)]  # full input rotation
    driver = {"joint": "drive", "pivot": {"instance": "ground", "connector": "o2"},
              "moving": {"instance": "input", "connector": "ja"}}
    poses = PlanarMotionSolver().solve(frames, joints, {"ground"}, plane, driver, values)
    assert len(poses) == len(values)
    # every frame closes the loop: the coupler's jb and rocker's jb stay coincident.
    for pose in poses:
        cj = _apply((_D, _C, 0.0), pose["coupler"])
        rj = _apply((_D, _C, 0.0), pose["rocker"])
        assert math.isclose(cj[0], rj[0], abs_tol=0.5)
        assert math.isclose(cj[1], rj[1], abs_tol=0.5)
    # the output rocker sweeps a non-trivial bounded arc (the loop transmits motion).
    angles = [math.degrees(math.atan2(pose["rocker"][0][1], pose["rocker"][0][0]))
              for pose in poses]
    assert (max(angles) - min(angles)) > 5.0


def _apply(p, m):
    return tuple(sum(p[k] * m[k][i] for k in range(3)) + m[3][i] for i in range(3))
