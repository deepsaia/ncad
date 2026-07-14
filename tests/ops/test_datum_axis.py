import pytest

from ncad.ops.datum_axis_params import DatumAxisParamError, datum_axis_kwargs


def test_two_point_axis():
    kw = datum_axis_kwargs(
        {"method": "two_point", "datum_points": [[0, 0, 0], [0, 0, 1]]}, {})
    assert kw["method"] == "two_point"
    assert kw["points"] == [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0)]


def test_two_point_needs_two():
    with pytest.raises(DatumAxisParamError):
        datum_axis_kwargs({"method": "two_point", "datum_points": [[0, 0, 0]]}, {})


def test_edge_method_shapes():
    kw = datum_axis_kwargs({"method": "edge", "edge": "pad.edge(3)"}, {})
    assert kw["method"] == "edge"


def test_unknown_method_raises():
    with pytest.raises(DatumAxisParamError):
        datum_axis_kwargs({"method": "wat"}, {})


def test_datum_axis_op_builds_reference_geometry():
    from ncad.ops.datum_axis_op import DatumAxisOp
    from tests.kernel.fake_kernel import FakeKernel

    params = {"id": "ax", "method": "two_point", "datum_points": [[0, 0, 0], [0, 0, 1]]}
    result = DatumAxisOp().build(None, params, {}, FakeKernel())
    assert result.shape is not None
    assert result.shape == ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert not any(i.level == "error" for i in result.issues)


@pytest.mark.slow
def test_datum_axis_feature_leaves_working_solid_unchanged():
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {
        "schema_version": 2, "units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5},
            {"id": "ax", "op": "datum_axis", "method": "two_point",
             "datum_points": [[0, 0, 0], [0, 0, 1]]},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    assert abs(kernel.signature(result.shape)["volume"] - 500.0) < 1e-6
