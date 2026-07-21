"""Path3dOp builds an open 3D wire; a sweep along it works (fake kernel)."""

import math

import pytest

from ncad.ops.path3d_op import Path3dOp
from ncad.ops.sweep_op import SweepOp
from tests.kernel.fake_kernel import FakeKernel


def test_polyline_wire_length():
    k = FakeKernel()
    result = Path3dOp().build(
        None, {"id": "p", "points": [[0, 0, 0], [30, 0, 0], [30, 0, 40]]}, {}, k)
    assert result.shape is not None
    assert result.shape.length == pytest.approx(30 + 40)


def test_bad_kind_is_a_build_issue():
    k = FakeKernel()
    result = Path3dOp().build(None, {"id": "p", "points": [[0, 0, 0], [1, 1, 1]],
                                     "kind": "arc3d"}, {}, k)
    assert result.shape is None
    assert result.issues and "unknown path3d kind" in result.issues[0].message


def test_sweep_along_3d_path_volume():
    # A square profile swept along a 3D L-bend: fake volume ~ area * path length.
    k = FakeKernel()
    square = k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY")
    path = Path3dOp().build(
        None, {"id": "cl", "points": [[0, 0, 0], [30, 0, 0], [30, 0, 40]]}, {}, k).shape
    result = SweepOp().build(
        square, {"id": "sw", "path": "cl", "__refs__": {"profile": square, "path": path}}, {}, k)
    assert result.shape is not None
    assert k.volume(result.shape) == pytest.approx(4 * (30 + 40), rel=1e-9)


def test_closed_polyline_returns_to_start():
    k = FakeKernel()
    result = Path3dOp().build(
        None, {"id": "p", "points": [[0, 0, 0], [10, 0, 0], [10, 10, 0]], "closed": True}, {}, k)
    # Closed triangle perimeter: 10 + 10 + sqrt(200).
    assert result.shape.length == pytest.approx(10 + 10 + math.sqrt(200))
