import copy

import pytest

pytestmark = pytest.mark.slow


def _doc() -> dict:
    return {
        "schema_version": 2, "units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
            {"id": "base", "op": "extrude", "profile": "sk", "distance": 20},
            {"id": "rnd", "op": "fillet", "edges": "select edges where created_by = 'base'",
             "radius": 2},
        ]}},
    }


def _build_volume(document: dict) -> float:
    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.ops.op_registry import OpRegistry

    kernel = Build123dKernel()
    builder = Builder(kernel, OpRegistry.with_defaults())
    result, _, _ = builder.build_part_mapped(document["parts"]["p"])
    assert result.shape is not None, [i.message for i in result.issues]
    return kernel.volume(result.shape)


def test_resize_baked_fillet_is_a_param_edit() -> None:
    # "Resize baked fillet" = edit the fillet feature's radius and rebuild; the persistent edge
    # selection still resolves, and the geometry changes (a bigger fillet removes more material).
    small = _build_volume(_doc())
    edited = copy.deepcopy(_doc())
    for feature in edited["parts"]["p"]["features"]:
        if feature["id"] == "rnd":
            feature["radius"] = 5
    big = _build_volume(edited)
    assert big != small  # a larger fillet changes the solid; the selection re-resolved cleanly
