"""Real kernel: wire3d builds a free 3D path; sweeping a profile along it yields a 3D solid."""

import pytest

from ncad.build.document_builder import DocumentBuilder
from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.kernel.kernel_op_error import KernelOpError

pytestmark = pytest.mark.slow

_L_BEND = [[0, 0, 0], [30, 0, 0], [40, 0, 10], [40, 0, 40]]


def _sweep_doc(kind: str) -> dict:
    return {"units": "mm", "parts": {"pipe": {"profile": "solid", "features": [
        {"id": "prof", "op": "sketch", "plane": "XY",
         "elements": [{"id": "c", "type": "circle", "d": 6.0}]},
        {"id": "cl", "op": "path3d", "kind": kind, "points": _L_BEND},
        {"id": "tube", "op": "sweep", "profile": "prof", "path": "cl"}]}}}


@pytest.mark.parametrize("kind", ["polyline", "spline"])
def test_sweep_along_3d_path_is_a_3d_solid(kind):
    kernel = Build123dKernel()
    result = DocumentBuilder(kernel).build(_sweep_doc(kind))["pipe"]
    assert result.shape is not None, [i.message for i in result.issues]
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(result.shape)
    # A genuine 3D path: the swept solid rises in Z (a planar XY sweep could not).
    assert maxz - minz > 30.0
    assert kernel.volume(result.shape) > 0.0


def test_wire3d_polyline_length_matches_segments():
    kernel = Build123dKernel()
    wire = kernel.wire3d([[0, 0, 0], [30, 0, 0], [30, 0, 40]], kind="polyline")
    assert wire.length == pytest.approx(70.0, rel=1e-6)


def test_wire3d_too_few_points_raises():
    with pytest.raises(KernelOpError, match="at least 2"):
        Build123dKernel().wire3d([[0, 0, 0]], kind="polyline")
