import math

import pytest

pytestmark = pytest.mark.slow


def _arm_x_heading(placement: list[list[float]]) -> float:
    # The moving body's local +X image is row 0 of the row-major pose; its heading in the x-y plane.
    row0 = placement[0]
    return math.degrees(math.atan2(row0[1], row0[0]))


def test_drive_to_point_rotates_a_revolute_body():
    from ncad.assembly.connector_frame import ConnectorFrame
    from ncad.assembly.mate_solver import MateSolver
    from ncad.assembly.motion_pins import driver_pins

    a = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    b = ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=10.0)
    bodies = {"base": {"pivot": a}, "arm": {"hub": b}}
    # revolute: concentric axes (arm origin on base axis + parallel), leaving rotation free.
    concentric = {"kind": "axes_coincident", "a": "A.axis", "b": "B.axis", "id": "rev",
                  "a_ref": {"instance": "base", "connector": "pivot"},
                  "b_ref": {"instance": "arm", "connector": "hub"}}
    for theta in (30.0, 90.0, 135.0):
        prims = [concentric] + driver_pins(
            "revolute", theta, {"instance": "base", "connector": "pivot"},
            {"instance": "arm", "connector": "hub"}, a, b)
        for p in prims:
            p.setdefault("id", "drive")
        out = MateSolver().solve(bodies, prims, {"base"}, {})
        assert out.status in ("solved", "under_constrained")
        assert math.isclose(_arm_x_heading(out.placements["arm"]), theta, abs_tol=1.0)
