import pytest


def test_revolve_about_datum_axis_resolves():
    # revolve_params previously raised on a reference axis; a resolved datum axis now works.
    from ncad.ops.revolve_params import revolve_kwargs

    kwargs = revolve_kwargs(
        {"axis": "datums.ax", "angle": 360},
        {"axis": ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))})
    assert kwargs["axis_dir"] == (0.0, 0.0, 1.0)
    assert kwargs["axis_point"] == (0.0, 0.0, 0.0)


@pytest.mark.slow
def test_sketch_on_datum_plane_builds():
    # A datum plane offset 10 above XY; a rectangle sketched on it extrudes to a solid whose
    # base sits near z=10 (the datum plane's height).
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            {"id": "d", "op": "datum_plane", "method": "offset", "base": "XY",
             "distance": 10.0},
            {"id": "sk", "op": "sketch", "plane": "datums.d",
             "elements": [{"id": "r", "type": "rectangle", "w": 8, "h": 8}]},
            {"id": "pad", "op": "extrude", "profile": "sk", "distance": 4},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    bbox = kernel.signature(result.shape)["bbox"]
    assert bbox[0][2] > 9.5   # base of the solid sits near z=10


@pytest.mark.slow
def test_revolve_about_datum_axis_end_to_end():
    # A profile revolved about a datum axis (two_point along Z) builds a solid of revolution.
    from ncad.build.document_builder import DocumentBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    doc = {"units": "mm",
        "parts": {"p": {"profile": "solid", "features": [
            # A datum axis parallel to Z but offset to x=-6, fully to one side of the profile
            # (the primitive rectangle is centered at origin, spanning x=[-2,2]), so revolving
            # about it is valid (no self-intersection through the axis).
            {"id": "ax", "op": "datum_axis", "method": "two_point",
             "datum_points": [[-6, 0, 0], [-6, 0, 1]]},
            {"id": "sk", "op": "sketch", "plane": "XZ",
             "elements": [{"id": "r", "type": "rectangle", "w": 4, "h": 10}]},
            {"id": "rev", "op": "revolve", "profile": "sk", "axis": "datums.ax",
             "angle": 360},
        ]}},
    }
    kernel = Build123dKernel()
    builder = DocumentBuilder(kernel)
    resolved = builder._resolve_and_validate(doc)
    result, _, _ = builder._builder.build_part_mapped(resolved["parts"]["p"])
    assert result.shape is not None
    assert kernel.signature(result.shape)["volume"] > 0
