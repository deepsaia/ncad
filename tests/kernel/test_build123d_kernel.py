"""Slow tests for the real build123d/OCP kernel and a full build → export.

Marked ``slow`` because importing OCP costs ~90s on first load. Run with ``-m slow``;
the fast suite deselects these with ``-m 'not slow'``.
"""

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


def test_unknown_export_extension_raises() -> None:
    from ncad.kernel.build123d_kernel import Build123dKernel

    kernel = Build123dKernel()
    solid = kernel.box(center=(0.0, 0.0, 0.0), size=(1.0, 1.0, 1.0))

    with pytest.raises(ValueError, match="unsupported"):
        kernel.export(solid, "model.unknownext")
