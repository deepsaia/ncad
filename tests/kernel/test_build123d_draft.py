import pytest

pytestmark = pytest.mark.slow


def _kernel():
    from ncad.kernel.build123d_kernel import Build123dKernel
    return Build123dKernel()


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def _vertical_faces(k, box):
    from ncad.ops.face_selector import FaceSelector
    faces = [d for d in k.describe_elements(box) if d["kind"] == "face"]
    return FaceSelector().select(faces, "vertical")


def test_draft_vertical_faces_builds():
    k = _kernel()
    box = _box(k)
    result = k.draft(box, _vertical_faces(k, box), angle=5.0, neutral="XY",
                     neutral_offset=0.0)
    assert k.volume(result) > 0


def test_draft_with_neutral_offset_builds():
    k = _kernel()
    box = _box(k)
    result = k.draft(box, _vertical_faces(k, box), angle=5.0, neutral="XY",
                     neutral_offset=10.0)
    assert k.volume(result) > 0


def test_draft_filters_non_planar_faces():
    # A plate with a cylindrical boss: the 'vertical' keyword selects the boss's cylindrical
    # wall alongside the planar sides. Draft is undefined on the cylinder and OCCT rejects
    # it; the kernel must filter to planar faces and still build (not crash or fail).
    k = _kernel()
    plate = k.extrude(k.polygon_face([(0, 0), (40, 0), (40, 40), (0, 40)], "XY"),
                      distance=8.0)
    boss = k.cylinder((20.0, 20.0, 8.0), "Z", 12.0, 15.0)
    solid = k.fuse([plate, boss])
    faces = [d for d in k.describe_elements(solid) if d["kind"] == "face"]
    from ncad.ops.face_selector import FaceSelector
    verticals = FaceSelector().select(faces, "vertical")
    # verticals include cylindrical boss wall(s); draft must skip them and taper the planes.
    result = k.draft(solid, verticals, angle=3.0, neutral="XY", neutral_offset=0.0)
    assert result.volume > 0


def test_draft_all_non_planar_faces_reports_error():
    # If NO planar face is selected (only a cylinder), draft raises rather than crashing.
    import pytest

    from ncad.kernel.kernel_op_error import KernelOpError
    k = _kernel()
    cyl = k.cylinder((0.0, 0.0, 0.0), "Z", 20.0, 20.0)
    faces = [d for d in k.describe_elements(cyl) if d["kind"] == "face"]
    from ncad.ops.face_selector import FaceSelector
    verticals = FaceSelector().select(faces, "vertical")  # the cylindrical wall
    with pytest.raises(KernelOpError, match="planar"):
        k.draft(cyl, verticals, angle=3.0, neutral="XY", neutral_offset=0.0)
