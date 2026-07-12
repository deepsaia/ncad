from tests.kernel.fake_kernel import FakeKernel


def test_fake_box_face_has_neighbours() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 10.0)
    descriptors = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"]
    target = descriptors[0]["handle"]
    neighbours = kernel.face_neighbours(solid, target)
    assert isinstance(neighbours, list)


def test_fake_box_face_not_tangent_adjacent() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 10.0)
    target = [d for d in kernel.describe_elements(solid) if d["kind"] == "face"][0]["handle"]
    assert kernel.is_tangent_adjacent(solid, target) is False


def test_fake_box_min_wall_thickness_is_positive() -> None:
    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)
    thickness = kernel.min_wall_thickness(solid)
    assert thickness is not None and thickness > 0
