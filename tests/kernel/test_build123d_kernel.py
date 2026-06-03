"""Slow tests for the real build123d/OCP kernel and a full build → export.

Marked ``slow`` because importing OCP costs ~90s on first load. Run with ``-m slow``;
the fast suite deselects these with ``-m 'not slow'``.
"""

import math

import pytest

pytestmark = pytest.mark.slow


def test_box_volume_and_centering() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    box = kernel.box(center=(0.0, 0.0, 0.0), size=(2.0, 4.0, 3.0))

    assert kernel.volume(box) == pytest.approx(24.0)
    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(box)
    assert (minx, miny, minz) == pytest.approx((-1.0, -2.0, -1.5))
    assert (maxx, maxy, maxz) == pytest.approx((1.0, 2.0, 1.5))


def test_prism_volume_and_bounds() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    # Triangular cross-section (base 6 at z=0, apex at z=2) extruded along x for 8m.
    profile = [(0.0, 0.0), (6.0, 0.0), (3.0, 2.0)]
    prism = kernel.prism(profile=profile, axis="x", start=0.0, end=8.0)

    assert kernel.volume(prism) == pytest.approx(48.0)  # 0.5*6*2*8
    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(prism)
    assert (minx, maxx) == pytest.approx((0.0, 8.0))  # extruded along x
    assert (miny, maxy) == pytest.approx((0.0, 6.0))  # cross-section base
    assert (minz, maxz) == pytest.approx((0.0, 2.0))  # apex height


def test_extrude_polygon_l_shape_volume_and_bounds() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    # L-shape: 6x6 minus a 3x3 top-right notch. Area = 27; height 2 → volume 54 exactly.
    l_shape = [(0, 0), (6, 0), (6, 3), (3, 3), (3, 6), (0, 6)]
    solid = kernel.extrude_polygon(polygon=l_shape, base_z=0.0, height=2.0)

    assert kernel.volume(solid) == pytest.approx(54.0)  # exact B-rep, not sampled
    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == pytest.approx((0.0, 0.0, 0.0))
    assert (maxx, maxy, maxz) == pytest.approx((6.0, 6.0, 2.0))


def test_sphere_and_barrel_and_intersect() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()

    s = kernel.sphere(center=(0.0, 0.0, 0.0), radius=3.0)
    assert kernel.volume(s) == pytest.approx((4 / 3) * math.pi * 27, rel=0.01)

    # Hemisphere via intersect with an upper half-box (z in [0,6]).
    upper = kernel.box(center=(0.0, 0.0, 3.0), size=(12.0, 12.0, 6.0))
    hemi = kernel.intersect([s, upper])
    assert kernel.volume(hemi) == pytest.approx((2 / 3) * math.pi * 27, rel=0.02)
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(hemi)
    assert minz == pytest.approx(0.0, abs=1e-6)
    assert maxz == pytest.approx(3.0, abs=1e-6)

    # Barrel vault along x: crown at base_z + radius, flat cut at base_z.
    barrel = kernel.barrel(start=(0.0, 0.0), end=(8.0, 0.0), radius=2.0, base_z=0.0)
    assert kernel.volume(barrel) > 0
    (_, _, bminz), (_, _, bmaxz) = kernel.bounding_box(barrel)
    assert bminz == pytest.approx(0.0, abs=1e-6)
    assert bmaxz == pytest.approx(2.0, abs=1e-6)


def test_extrude_rounded_polygon_smaller_than_sharp() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    sharp = kernel.extrude_polygon(polygon=square, base_z=0.0, height=3.0)
    rounded = kernel.extrude_rounded_polygon(
        polygon=square, corner_radii={2: 1.0}, base_z=0.0, height=3.0
    )

    # Rounding corner (4,4) removes a corner sliver: ~(1 - pi/4) * r^2 * height.
    sharp_v = kernel.volume(sharp)
    rounded_v = kernel.volume(rounded)
    assert rounded_v < sharp_v
    removed = sharp_v - rounded_v
    expected_removed = (1 - math.pi / 4) * 1.0**2 * 3.0
    assert removed == pytest.approx(expected_removed, rel=0.05)


def test_extrude_rounded_polygon_only_one_corner_shrinks() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    rounded = kernel.extrude_rounded_polygon(
        polygon=square, corner_radii={2: 1.0}, base_z=0.0, height=3.0
    )
    # The other three corners are still sharp → bbox is unchanged 4x4x3.
    (minx, miny, _), (maxx, maxy, _) = kernel.bounding_box(rounded)
    assert (minx, miny, maxx, maxy) == pytest.approx((0.0, 0.0, 4.0, 4.0))


def test_arc_wall_volume_and_height() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    wall = kernel.arc_wall(
        center=(0.0, 0.0), radius=3.0, start_angle=0.0, end_angle=90.0,
        base_z=0.0, height=3.0, thickness=0.2,
    )
    expected = 3.0 * (math.pi / 2) * 0.2 * 3.0  # arc length * thickness * height
    assert kernel.volume(wall) == pytest.approx(expected, rel=0.05)
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(wall)
    assert (minz, maxz) == pytest.approx((0.0, 3.0))


def test_extrude_polygon_square_equals_box() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    poly_solid = kernel.extrude_polygon(polygon=square, base_z=0.0, height=3.0)
    box_solid = kernel.box(center=(2.0, 2.0, 1.5), size=(4.0, 4.0, 3.0))

    assert kernel.volume(poly_solid) == pytest.approx(kernel.volume(box_solid))


def test_union_then_subtract_volumes() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    a = kernel.box(center=(0.0, 0.0, 0.0), size=(4.0, 4.0, 4.0))
    b = kernel.box(center=(2.0, 0.0, 0.0), size=(4.0, 4.0, 4.0))

    union = kernel.union([a, b])
    assert kernel.volume(union) == pytest.approx(96.0)

    tool = kernel.box(center=(0.0, 0.0, 0.0), size=(2.0, 2.0, 2.0))
    diff = kernel.subtract(union, [tool])
    assert kernel.volume(diff) < kernel.volume(union)


def test_export_gltf_and_step(tmp_path) -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    solid = kernel.box(center=(0.0, 0.0, 0.0), size=(2.0, 2.0, 2.0))

    gltf = tmp_path / "m.gltf"
    step = tmp_path / "m.step"
    kernel.export(solid, str(gltf))
    kernel.export(solid, str(step))

    assert gltf.exists() and gltf.stat().st_size > 0
    assert step.exists() and step.stat().st_size > 0


def test_end_to_end_generate_build_export(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.generate.generator import Generator
    from ncad.kernel.build123d_kernel import Build123dKernel

    spec = Generator({"width": 12.0, "depth": 9.0, "num_rooms": 4}).generate(seed=42)
    kernel = Build123dKernel()

    solid = Builder(kernel).build(spec)
    assert kernel.volume(solid) > 0

    out = tmp_path / "box_house.gltf"
    kernel.export(solid, str(out))
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.parametrize("shape", ["L", "T", "U"])
def test_rounded_shapes_build_and_export(shape, tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.generate.generator import Generator
    from ncad.kernel.build123d_kernel import Build123dKernel

    params = {
        "width": 12.0,
        "depth": 9.0,
        "num_rooms": 5,
        "footprint_shape": shape,
        "corner_radius": 1.0,
    }
    spec = Generator(params).generate(seed=42)
    kernel = Build123dKernel()

    solid = Builder(kernel).build(spec)  # both convex + concave arc walls build
    assert kernel.volume(solid) > 0

    out = tmp_path / f"rounded_{shape}.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_brief_with_balcony_builds(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.compile.spec_compiler import SpecCompiler
    from ncad.kernel.build123d_kernel import Build123dKernel

    # Two-storey building with a balcony on the upper floor (railing rods etc.).
    brief = {
        "footprint": [[0, 0], [10, 0], [10, 7], [0, 7]],
        "rounded_corners": {},
        "num_rooms": 4,
        "num_storeys": 2,
        "storey_height": 3.0,
        "roof": "flat",
        "balconies": [{"storey": 1, "wall": 0, "along": 0.5, "length": 3.0, "depth": 1.5}],
    }
    kernel = Build123dKernel()
    solid = Builder(kernel).build(SpecCompiler().compile(brief))

    assert kernel.volume(solid) > 0
    out = tmp_path / "brief_balcony.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_brief_with_hip_roof_builds(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.compile.spec_compiler import SpecCompiler
    from ncad.kernel.build123d_kernel import Build123dKernel

    brief = {
        "footprint": [[0, 0], [12, 0], [12, 9], [0, 9]],
        "rounded_corners": {},
        "num_rooms": 4,
        "storey_height": 3.0,
        "roof": "hip",
    }
    kernel = Build123dKernel()
    solid = Builder(kernel).build(SpecCompiler().compile(brief))

    assert kernel.volume(solid) > 0
    out = tmp_path / "brief_hip.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_brief_with_gable_roof_builds(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.compile.spec_compiler import SpecCompiler
    from ncad.kernel.build123d_kernel import Build123dKernel

    # An agent brief: rectangle + gable roof, round numbers only.
    brief = {
        "footprint": [[0, 0], [12, 0], [12, 9], [0, 9]],
        "rounded_corners": {},
        "num_rooms": 4,
        "storey_height": 3.0,
        "roof": "gable",
    }
    kernel = Build123dKernel()
    solid = Builder(kernel).build(SpecCompiler().compile(brief))

    assert kernel.volume(solid) > 0
    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz > 3.5  # gable apex above the flat wall top

    out = tmp_path / "brief_gable.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_irregular_mixed_corner_hocon_builds(tmp_path) -> None:
    from pathlib import Path

    from ncad.build.builder import Builder
    from ncad.kernel.build123d_kernel import Build123dKernel
    from ncad.spec.spec_loader import SpecLoader

    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    spec = SpecLoader().load(str(fixtures / "irregular_house.hocon"))
    kernel = Build123dKernel()

    # Irregular hexagon: diagonal straight walls + a mix of sharp and rounded corners.
    solid = Builder(kernel).build(spec)
    assert kernel.volume(solid) > 0

    out = tmp_path / "irregular.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_l_footprint_builds_with_empty_notch(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.generate.generator import Generator
    from ncad.kernel.build123d_kernel import Build123dKernel

    spec = Generator(
        {"width": 12.0, "depth": 9.0, "num_rooms": 4, "footprint_shape": "L"}
    ).generate(seed=42)
    kernel = Build123dKernel()

    solid = Builder(kernel).build(spec)
    assert kernel.volume(solid) > 0

    # The slab/roof follow the L polygon, so the model's footprint area (slab volume /
    # thickness) is strictly less than the 12x9 bounding box. Compare against bbox slab.
    footprint = spec["storeys"][0]["footprint"]
    poly_area = abs(_shoelace(footprint))
    assert poly_area < 12.0 * 9.0  # notch removed

    out = tmp_path / "l_house.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def _shoelace(polygon) -> float:
    area = 0.0
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2.0


def test_gable_roof_builds_and_exports(tmp_path) -> None:
    from ncad.build.builder import Builder
    from ncad.generate.generator import Generator
    from ncad.kernel.build123d_kernel import Build123dKernel

    spec = Generator({"width": 12.0, "depth": 9.0, "num_rooms": 4}).generate(seed=42)
    spec["roof"] = {"kind": "gable", "pitch": 0.5}  # real pitched roof through the Builder
    kernel = Build123dKernel()

    solid = Builder(kernel).build(spec)

    assert kernel.volume(solid) > 0
    # Roof apex rises above the flat wall top (3.0 storey height).
    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz > 3.5

    out = tmp_path / "gable_house.glb"
    kernel.export(solid, str(out))
    assert out.exists() and out.read_bytes()[:4] == b"glTF"


def test_unknown_export_extension_raises() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    solid = kernel.box(center=(0.0, 0.0, 0.0), size=(1.0, 1.0, 1.0))

    with pytest.raises(ValueError, match="unsupported"):
        kernel.export(solid, "model.unknownext")
