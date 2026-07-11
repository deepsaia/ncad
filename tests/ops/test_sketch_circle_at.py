import pytest

from ncad.ops.sketch_op import SketchOp
from tests.kernel.fake_kernel import FakeKernel


def _sketch(kernel, element):
    return SketchOp().build(None, {"id": "sk", "op": "sketch", "plane": "XY",
                                   "elements": [element]}, {}, kernel).shape


def test_circle_defaults_to_origin():
    k = FakeKernel()
    face = _sketch(k, {"id": "c", "type": "circle", "d": 10})
    (minx, miny, _), (maxx, maxy, _) = k.bounding_box(k.extrude(face, 1))
    assert (minx + maxx) / 2 == pytest.approx(0.0, abs=1e-6)
    assert (miny + maxy) / 2 == pytest.approx(0.0, abs=1e-6)


def test_circle_at_places_center():
    k = FakeKernel()
    face = _sketch(k, {"id": "c", "type": "circle", "d": 10, "at": [22, 5]})
    (minx, miny, _), (maxx, maxy, _) = k.bounding_box(k.extrude(face, 1))
    assert (minx + maxx) / 2 == pytest.approx(22.0, abs=1e-6)
    assert (miny + maxy) / 2 == pytest.approx(5.0, abs=1e-6)
