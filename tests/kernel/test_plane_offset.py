from tests.kernel.fake_kernel import FakeKernel


def test_polygon_face_carries_offset():
    k = FakeKernel()
    face = k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY", offset=40.0)
    assert face.offset == 40.0


def test_polygon_face_offset_defaults_zero():
    k = FakeKernel()
    face = k.polygon_face([(0, 0), (2, 0), (2, 2), (0, 2)], "XY")
    assert face.offset == 0.0


def test_wire_face_carries_offset():
    k = FakeKernel()
    edges = [{"kind": "line", "points": [(0, 0), (2, 0)]},
             {"kind": "line", "points": [(2, 0), (2, 2)]},
             {"kind": "line", "points": [(2, 2), (0, 0)]}]
    face = k.wire_face(edges, "XY", offset=15.0)
    assert face.offset == 15.0
