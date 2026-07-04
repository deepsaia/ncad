import pytest

from ncad.build.document_builder import DocumentBuilder
from tests.kernel.fake_kernel import FakeKernel


def _rounded_bar():
    # a bar 40 long, 20 tall, with two semicircular ends: a stadium/slot shape
    return {"schema_version": 1, "units": "mm", "parts": {"p": {
        "profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "entities": [
                 {"id": "a", "type": "point", "at": [0, 0]},
                 {"id": "b", "type": "point", "at": [40, 0]},
                 {"id": "sl", "type": "slot", "p1": "a", "p2": "b", "width": 20}],
             "constraints": []},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5}]}}}


def test_slot_sketch_builds_on_fake_kernel():
    result = DocumentBuilder(FakeKernel()).build(_rounded_bar())["p"]
    assert result.shape is not None
    errors = [i for i in result.issues if i.level == "error"]
    assert errors == []


@pytest.mark.slow
def test_slot_sketch_exports_on_real_kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel

    result = DocumentBuilder(Build123dKernel()).build(_rounded_bar())["p"]
    assert result.shape is not None
    assert Build123dKernel().volume(result.shape) > 0
