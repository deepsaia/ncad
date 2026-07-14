import pytest

pytestmark = pytest.mark.slow


def test_curve_pattern_along_a_sketch_path_builds_multiple_bodies():
    # A small block patterned along an open-sketch PATH (a real finite curve) keeps 4 bodies.
    # A curve pattern follows a finite path (an edge / open sketch), not an infinite datum
    # axis: the path carries the extent the instances are spaced along.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {
        "schema_version": 2, "units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "path_sk", "op": "sketch", "plane": "XY", "open": True,
             "entities": [{"id": "a", "type": "point", "at": [0, 0]},
                          {"id": "c", "type": "point", "at": [30, 0]},
                          {"id": "ln", "type": "line", "p1": "a", "p2": "c"}],
             "constraints": [{"type": "fix", "of": "a"}, {"type": "fix", "of": "c"}]},
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 3, "h": 3}]},
            {"id": "blk", "op": "extrude", "profile": "sk", "distance": 3},
            {"id": "row", "op": "pattern", "kind": "curve", "path": "path_sk",
             "count": 4, "merge": False},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    bodies = kernel.bodies(result.shape)
    assert len(bodies) == 4
    # The last instance sits near x=30 (the far end of the 30mm path).
    max_x = max(kernel.bounding_box(body.shape)[1][0] for body in bodies)
    assert max_x > 29.0
