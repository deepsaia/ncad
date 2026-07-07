import pytest

from ncad.ops.sweep_op import SweepOp
from tests.kernel.fake_kernel import FakeKernel


def _square(k):
    return k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY")


def _path(k):
    return k.wire([{"kind": "line", "points": [(0.0, 0.0), (0.0, 10.0)]}], "XZ")


def test_sweep_single_path_volume():
    k = FakeKernel()
    result = SweepOp().build(
        _square(k), {"id": "sw", "path": "path_sk",
                     "__refs__": {"profile": _square(k), "path": _path(k)}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) == pytest.approx(4 * 10, rel=1e-9)


def test_sweep_helix_volume():
    k = FakeKernel()
    result = SweepOp().build(
        _square(k),
        {"id": "coil", "helix": {"pitch": 5, "height": 40, "radius": 12, "axis": "Z"},
         "__refs__": {"profile": _square(k)}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) > 0


def test_sweep_missing_path_source_reports_issue():
    k = FakeKernel()
    result = SweepOp().build(_square(k), {"id": "sw", "__refs__": {"profile": _square(k)}},
                             {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)


def test_sweep_path_source_ref_missing_reports_issue():
    k = FakeKernel()
    result = SweepOp().build(
        _square(k), {"id": "sw", "path": "path_sk", "__refs__": {"profile": _square(k)}},
        {}, k)
    assert result.shape is None and any(i.level == "error" for i in result.issues)
