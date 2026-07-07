import math

import pytest

from ncad.ops.revolve_op import RevolveOp
from tests.kernel.fake_kernel import FakeKernel


def _offset_rect(k):
    return k.polygon_face([(8, 0), (12, 0), (12, 2), (8, 2)], "XY")


def test_revolve_builds_pappus_volume():
    k = FakeKernel()
    result = RevolveOp().build(_offset_rect(k), {"id": "rev", "axis": "Y"}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) == pytest.approx(8 * 2 * math.pi * 10, rel=1e-9)


def test_revolve_no_input_face_reports_issue():
    k = FakeKernel()
    result = RevolveOp().build(None, {"id": "rev", "axis": "Y"}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_revolve_unknown_axis_reports_issue():
    k = FakeKernel()
    result = RevolveOp().build(_offset_rect(k), {"id": "rev", "axis": "W"}, {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
