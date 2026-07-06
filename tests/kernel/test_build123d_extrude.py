import pytest


@pytest.mark.slow
def test_symmetric_same_volume_as_blind():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    blind = k.extrude(k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 4)
    sym = k.extrude(k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 4,
                    symmetric=True)
    assert k.volume(sym) == pytest.approx(k.volume(blind), rel=1e-6)


@pytest.mark.slow
def test_two_side_sums_distances():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    face = k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = k.extrude(face, 4, second_distance=3)
    assert k.volume(solid) == pytest.approx(10 * 10 * 7, rel=1e-6)


@pytest.mark.slow
def test_thin_wall_volume():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    face = k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = k.extrude(face, 10, thin=2)
    # a 2-wide wall around a 10x10 profile: (100 - 36) * 10 = 640
    assert k.volume(solid) == pytest.approx(640.0, rel=1e-6)


@pytest.mark.slow
def test_draft_changes_volume():
    from ncad.kernel.build123d_kernel import Build123dKernel
    k = Build123dKernel()
    straight = k.volume(k.extrude(
        k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 5))
    tapered = k.volume(k.extrude(
        k.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY"), 5, draft=10))
    assert tapered != pytest.approx(straight, rel=1e-6)
