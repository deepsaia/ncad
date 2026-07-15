import math

import pytest


def _doc(features):
    return {"schema_version": 2, "units": "mm",
            "parts": {"p": {"profile": "solid", "features": features}}}


def test_primitive_base_body_builds_on_fake():
    from ncad.build.document_builder import DocumentBuilder
    from tests.kernel.fake_kernel import FakeKernel

    doc = _doc([{"id": "ball", "op": "primitive", "kind": "sphere", "d": 20}])
    result = DocumentBuilder(FakeKernel()).build(doc)["p"]
    assert result.shape is not None
    assert math.isclose(FakeKernel().volume(result.shape),
                        4.0 / 3.0 * math.pi * 1000.0, rel_tol=1e-6)


@pytest.mark.slow
def test_primitive_then_boolean_composes_on_real_kernel():
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = _doc([
        # Center the box on the origin (at = -w/2, -d/2) so the centered hole is fully inside.
        {"id": "base", "op": "primitive", "kind": "box", "w": 40, "d": 40, "h": 10,
         "at": [-20, -20]},
        {"id": "hole_sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "c", "type": "circle", "d": 12}]},
        {"id": "pin", "op": "extrude", "profile": "hole_sk", "distance": 10},
        {"id": "cut", "op": "boolean", "operation": "cut", "target": "base", "tool": "pin"},
    ])
    result = DocumentBuilder(Build123dKernel()).build(doc)["p"]
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]
    # 40x40x10 box minus a d12 through hole.
    expected = 40 * 40 * 10 - math.pi * 36 * 10
    assert abs(Build123dKernel().volume(result.shape) - expected) < 1.0
