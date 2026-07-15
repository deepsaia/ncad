import math

from tests.kernel.fake_kernel import FakeKernel


def _box(kernel, w=20.0, d=10.0, h=5.0):
    return kernel.extrude(kernel.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY"), h)


def test_fake_oriented_bounding_box_shape():
    kernel = FakeKernel()
    obb = kernel.oriented_bounding_box(_box(kernel))
    assert set(obb) == {"size", "center", "axes"}
    assert len(obb["size"]) == 3 and len(obb["center"]) == 3
    assert len(obb["axes"]) == 3 and all(len(a) == 3 for a in obb["axes"])
    # Axes are orthonormal (the Fake returns world X/Y/Z).
    for a in obb["axes"]:
        assert math.isclose(math.hypot(*a), 1.0, abs_tol=1e-9)
