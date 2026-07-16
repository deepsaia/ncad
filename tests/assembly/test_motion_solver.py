import math

import pytest

pytestmark = pytest.mark.slow


def _arm_x_heading(placement: list[list[float]]) -> float:
    row0 = placement[0]
    return math.degrees(math.atan2(row0[1], row0[0]))


def test_motion_solver_sweeps_a_revolute():
    from ncad.assembly.connector_frame import ConnectorFrame
    from ncad.assembly.motion_pins import driver_pins
    from ncad.assembly.motion_solver import MotionSolver

    a = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    b = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    bodies = {"base": {"pivot": a}, "arm": {"hub": b}}
    concentric = {"kind": "axes_coincident", "a": "A.axis", "b": "B.axis", "id": "rev",
                  "a_ref": {"instance": "base", "connector": "pivot"},
                  "b_ref": {"instance": "arm", "connector": "hub"}}
    values = [0.0, 45.0, 90.0, 135.0]
    per_value = []
    for theta in values:
        pins = driver_pins("revolute", theta, {"instance": "base", "connector": "pivot"},
                           {"instance": "arm", "connector": "hub"}, a, b)
        for p in pins:
            p.setdefault("id", "drive")
        per_value.append(pins)
    outcomes = MotionSolver().solve(bodies, [concentric], {"base"}, {}, per_value)
    assert len(outcomes) == len(values)
    for theta, out in zip(values, outcomes):
        assert math.isclose(_arm_x_heading(out.placements["arm"]), theta, abs_tol=1.0)
