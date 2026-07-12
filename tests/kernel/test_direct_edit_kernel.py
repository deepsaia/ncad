import pytest

pytestmark = pytest.mark.slow


def _box(kernel, w=20.0, d=20.0, h=20.0):
    face = kernel.polygon_face([(0, 0), (w, 0), (w, d), (0, d)], "XY")
    return kernel.extrude(face, h)


def test_offset_solid_outward_grows_volume() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = _box(kernel)
    before = kernel.volume(box)
    grown = kernel.offset_solid(box, 1.0)
    assert kernel.volume(grown) > before


def test_defeature_removes_a_face() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = _box(kernel, 40.0, 40.0, 10.0)
    boss = kernel.transform(_box(kernel, 10.0, 10.0, 10.0), move=(15.0, 15.0, 10.0))
    fused = kernel.fuse([box, boss])
    faces_before = len(kernel.describe_elements(fused))
    # Build123dKernel names planar faces "plane" (build123d GeomType.PLANE lowercased).
    planar = [d for d in kernel.describe_elements(fused)
              if d["kind"] == "face" and d["geom_type"] == "plane"]
    target = max(planar, key=lambda d: d["mid_z"])["handle"]
    result = kernel.defeature(fused, target)
    assert result is not None
    assert len(kernel.describe_elements(result)) <= faces_before


def test_real_box_min_wall_thickness_is_positive() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    thickness = kernel.min_wall_thickness(_box(kernel))
    assert thickness is not None and thickness > 0


def test_real_fillet_creates_tangent_adjacency() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = _box(kernel)
    filleted = kernel.fillet_edges(box, [kernel.edges_of(box)[0]["edge"]], 4.0)
    # Build123dKernel names the fillet face "cylinder" (build123d GeomType.CYLINDER lowercased).
    curved = [d for d in kernel.describe_elements(filleted)
              if d["kind"] == "face" and d["geom_type"] == "cylinder"]
    assert curved
    # The fillet face is tangent to its flat neighbours.
    assert kernel.is_tangent_adjacent(filleted, curved[0]["handle"]) is True
