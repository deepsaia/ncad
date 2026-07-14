import pytest

from ncad.ops.datum_plane_params import DatumPlaneParamError, datum_plane_kwargs


def test_offset_from_base_plane():
    kw = datum_plane_kwargs({"method": "offset", "base": "XY", "distance": 10.0}, {})
    assert kw["method"] == "offset" and kw["base"] == "XY" and kw["distance"] == 10.0


def test_base_plane_without_method_defaults_to_offset():
    kw = datum_plane_kwargs({"base": "XZ", "distance": 4.0}, {})
    assert kw["method"] == "offset" and kw["base"] == "XZ"


def test_three_point_requires_three_points():
    with pytest.raises(DatumPlaneParamError):
        datum_plane_kwargs(
            {"method": "three_point", "datum_points": [[0, 0, 0], [1, 0, 0]]}, {})


def test_three_point_shapes_points():
    kw = datum_plane_kwargs(
        {"method": "three_point", "datum_points": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]}, {})
    assert kw["points"] == [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]


def test_unknown_method_raises():
    with pytest.raises(DatumPlaneParamError):
        datum_plane_kwargs({"method": "wat"}, {})


def test_datum_plane_op_builds_reference_geometry():
    from ncad.ops.datum_plane_op import DatumPlaneOp
    from tests.kernel.fake_kernel import FakeKernel

    params = {"id": "d", "method": "offset", "base": "XY", "distance": 10.0}
    result = DatumPlaneOp().build(None, params, {}, FakeKernel())
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)


@pytest.mark.slow
def test_datum_plane_feature_leaves_working_solid_unchanged():
    # A box extrude followed by a datum_plane feature: the datum is reference geometry, so
    # the part's built solid is still the box (the datum does not become the working solid).
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {
        "schema_version": 2, "units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5},
            {"id": "d", "op": "datum_plane", "method": "offset", "base": "XY",
             "distance": 20.0},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    assert abs(kernel.signature(result.shape)["volume"] - 500.0) < 1e-6
