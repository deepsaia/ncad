import pytest

pytestmark = pytest.mark.slow


def test_fill_pattern_over_a_face_builds_many_bodies():
    # A fill pattern replicates the running solid over a region FACE of that solid. Here a
    # plate is filled over its own top face at a spacing, kept as separate bodies (the grid of
    # placements). The region face must belong to the running solid (a distinct feature over a
    # distinct part's face is feature-pattern, which is Phase 4).
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "plate_sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 24}]},
            {"id": "plate", "op": "extrude", "profile": "plate_sk", "distance": 2},
            {"id": "field", "op": "pattern", "kind": "fill",
             "region": "select faces where normal_z > 0.9 and area > 100",
             "spacing": 10, "merge": False},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    # A 40x24 face at spacing 10 places a grid of instances.
    assert len(kernel.bodies(result.shape)) > 4
