import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel


def _doc():
    return {"units": "mm", "parts": {"p": {
        "profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "entities": [
                 {"id": "p0", "type": "point", "at": [0, 0]},
                 {"id": "p1", "type": "point", "at": [30, 2]},
                 {"id": "p2", "type": "point", "at": [31, 33]},
                 {"id": "p3", "type": "point", "at": [1, 29]},
                 {"id": "l0", "type": "line", "p1": "p0", "p2": "p1"},
                 {"id": "l1", "type": "line", "p1": "p1", "p2": "p2"},
                 {"id": "l2", "type": "line", "p1": "p2", "p2": "p3"},
                 {"id": "l3", "type": "line", "p1": "p3", "p2": "p0"}],
             "constraints": [
                 {"type": "horizontal", "of": "l0"},
                 {"type": "vertical", "of": "l1"},
                 {"type": "horizontal", "of": "l2"},
                 {"type": "vertical", "of": "l3"},
                 {"type": "distance", "points": ["p0", "p1"], "value": 40},
                 {"type": "distance", "points": ["p1", "p2"], "value": 40}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5}]}}}


def test_constrained_sketch_builds_on_fake_kernel():
    result = DocumentBuilder(FakeKernel()).build(_doc())["p"]
    assert result.shape is not None
    # a 40 x 40 square extruded 5 = 8000 (may carry an under-constrained warning)
    assert FakeKernel().volume(result.shape) == pytest.approx(8000.0)
    assert all(i.level == "warning" for i in result.issues)


@pytest.mark.slow
def test_constrained_sketch_is_deterministic_on_real_kernel():
    from ncad.build.equality_comparator import EqualityComparator
    from ncad.kernel.build123d_kernel import Build123dKernel

    a = DocumentBuilder(Build123dKernel()).build(_doc())["p"].shape
    b = DocumentBuilder(Build123dKernel()).build(_doc())["p"].shape
    assert a is not None and b is not None
    assert EqualityComparator().equal(Build123dKernel().signature(a),
                                      Build123dKernel().signature(b))
