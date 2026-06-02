"""Tests for the pure Builder, run against the fake kernel (no OCP import).

These assert builder *logic* — that walls/openings/roof/slab produce the right solids
and that openings reduce volume — without the heavy CAD backend. Real-geometry and
export are exercised separately in the slow build123d kernel test.
"""

import pytest

from ncad.build.builder import Builder
from tests.kernel.fake_kernel import FakeKernel


def _spec(with_opening: bool = False) -> dict:
    wall = {
        "id": "wall_0",
        "start": [0.0, 0.0],
        "end": [6.0, 0.0],
        "thickness": 0.2,
    }
    if with_opening:
        wall["openings"] = [
            {"id": "door_0", "kind": "door", "along": 0.5, "width": 1.0, "height": 2.1, "sill": 0.0}
        ]
    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [wall],
                "rooms": [{"id": "room_0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_build_returns_a_solid_with_positive_volume() -> None:
    kernel = FakeKernel()

    solid = Builder(kernel).build(_spec())

    assert kernel.volume(solid) > 0


def test_build_is_pure_same_spec_same_geometry_signature() -> None:
    kernel = FakeKernel()
    spec = _spec()

    a = Builder(kernel).build(spec)
    b = Builder(kernel).build(spec)

    assert kernel.bounding_box(a) == kernel.bounding_box(b)
    assert kernel.volume(a) == pytest.approx(kernel.volume(b))


def test_opening_reduces_volume() -> None:
    kernel = FakeKernel()

    without = kernel.volume(Builder(kernel).build(_spec(with_opening=False)))
    with_door = kernel.volume(Builder(kernel).build(_spec(with_opening=True)))

    assert with_door < without


def test_wall_height_defaults_to_storey_height() -> None:
    kernel = FakeKernel()
    spec = _spec()

    solid = Builder(kernel).build(spec)

    # Top of geometry should reach storey height + roof slab.
    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz == pytest.approx(3.0 + 0.2, rel=0.02)


def test_unknown_roof_kind_raises() -> None:
    kernel = FakeKernel()
    spec = _spec()
    spec["roof"]["kind"] = "dome"

    with pytest.raises(ValueError, match="roof"):
        Builder(kernel).build(spec)


def test_export_writes_file(tmp_path) -> None:
    kernel = FakeKernel()
    out = tmp_path / "model.txt"

    builder = Builder(kernel)
    solid = builder.build(_spec())
    kernel.export(solid, str(out))

    assert out.exists()
