import pytest

from ncad.ops.feature_mirror_params import FeatureMirrorParamError, feature_mirror_kwargs


def test_kwargs_base_plane_and_operation():
    kw = feature_mirror_kwargs({"operation": "union", "plane": "YZ"}, {})
    assert kw["operation"] == "union"
    assert kw["plane"]["kind"] == "base" and kw["plane"]["plane"] == "YZ"


def test_operation_defaults_to_cut():
    kw = feature_mirror_kwargs({"plane": "XZ"}, {})
    assert kw["operation"] == "cut"


def test_operation_must_be_cut_or_union():
    with pytest.raises(FeatureMirrorParamError):
        feature_mirror_kwargs({"operation": "wat", "plane": "XY"}, {})


@pytest.mark.slow
def test_feature_mirror_unions_a_reflected_boss():
    # A boss tool on the +x side is mirrored across YZ and unioned, adding a symmetric boss on
    # the -x side. The boss tool is built before the plate so the plate is the running solid.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"schema_version": 2, "units": "mm",
           "parts": {"p": {"profile": "solid", "features": [
               {"id": "boss_sk", "op": "sketch", "plane": "XY",
                "elements": [{"id": "c", "type": "circle", "d": 8, "at": [20, 0]}]},
               {"id": "boss", "op": "extrude", "profile": "boss_sk", "distance": 10},
               {"id": "plate_sk", "op": "sketch", "plane": "XY",
                "elements": [{"id": "r", "type": "rectangle", "w": 60, "h": 20}]},
               {"id": "plate", "op": "extrude", "profile": "plate_sk", "distance": 4},
               {"id": "with_boss", "op": "boolean", "operation": "union",
                "target": "plate", "tool": "boss"},
               {"id": "mirror_boss", "op": "feature_mirror", "tool": "boss",
                "operation": "union", "plane": "YZ"},
           ]}}}
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    bbox = kernel.signature(result.shape)["bbox"]
    # The mirrored boss reaches the -x side (a cylinder near x=-20).
    assert bbox[0][0] < -20.0
