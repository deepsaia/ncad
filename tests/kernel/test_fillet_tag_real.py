import pytest

pytestmark = pytest.mark.slow


def test_fillet_face_gets_fillet_tag_on_real_kernel() -> None:
    # The 4.1 tagger used "cylindrical", which never matched build123d's "cylinder", so fillet
    # faces were never tagged. After canonicalization the fillet face is tagged "fillet".
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.refs.generative_tagger import GenerativeTagger

    kernel = Build123dKernel()
    box = kernel.extrude(kernel.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"), 20.0)
    filleted = kernel.fillet_edges(box, [kernel.edges_of(box)[0]["edge"]], 4.0)
    faces = [d for d in kernel.describe_elements(filleted) if d["kind"] == "face"]
    tags = GenerativeTagger().tags_for("fillet", "XY", faces)
    assert "fillet" in tags.values()
