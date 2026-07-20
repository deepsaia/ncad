import pytest

pytestmark = pytest.mark.slow


def test_mirror_across_a_model_face_builds():
    # A block mirrored across one of its own end faces (keep + no merge) yields 2 bodies: the
    # original and its reflection on the far side of that face.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "sk", "op": "sketch", "plane": "XY",
             "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
            {"id": "blk", "op": "extrude", "profile": "sk", "distance": 6},
            {"id": "mir", "op": "mirror",
             "face": "select faces where normal_x > 0.9", "keep": True, "merge": False},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    assert len(kernel.bodies(result.shape)) == 2
