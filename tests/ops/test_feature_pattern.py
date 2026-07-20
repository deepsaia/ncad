import pytest

from ncad.ops.feature_pattern_params import FeaturePatternParamError, feature_pattern_kwargs


def test_kwargs_wraps_pattern_placement_and_operation():
    kw = feature_pattern_kwargs({"operation": "cut", "kind": "linear",
                                 "x": {"dir": [1, 0, 0], "spacing": 10, "count": 3}})
    assert kw["operation"] == "cut"
    assert kw["pattern"]["kind"] == "linear"


def test_operation_defaults_to_cut():
    kw = feature_pattern_kwargs({"kind": "linear",
                                 "x": {"dir": [1, 0, 0], "spacing": 10, "count": 2}})
    assert kw["operation"] == "cut"


def test_operation_must_be_cut_or_union():
    with pytest.raises(FeaturePatternParamError):
        feature_pattern_kwargs({"operation": "wat", "kind": "linear",
                                "x": {"dir": [1, 0, 0], "spacing": 10, "count": 2}})


@pytest.mark.slow
def test_feature_pattern_cuts_a_row_of_holes():
    # The tool feature (cutter) is built BEFORE the plate so the PLATE is the running solid at
    # the feature_pattern (which patterns the cutter tool and cuts the plate). See ordering
    # rule 12e.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"units": "mm",
           "parts": {"p": {"profile": "solid", "features": [
               {"id": "cutter_sk", "op": "sketch", "plane": "XY",
                "elements": [{"id": "c", "type": "circle", "d": 5, "at": [-20, 0]}]},
               {"id": "cutter", "op": "extrude", "profile": "cutter_sk", "distance": 6},
               {"id": "plate_sk", "op": "sketch", "plane": "XY",
                "elements": [{"id": "r", "type": "rectangle", "w": 60, "h": 20}]},
               {"id": "plate", "op": "extrude", "profile": "plate_sk", "distance": 6},
               {"id": "holes", "op": "feature_pattern", "tool": "cutter", "operation": "cut",
                "kind": "linear", "x": {"dir": [1, 0, 0], "spacing": 20, "count": 3}},
           ]}}}
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    assert kernel.signature(result.shape)["surface_types"].get("cylinder") == 3
