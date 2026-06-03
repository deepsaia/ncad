"""Tests for the pure Builder, run against the fake kernel (no OCP import).

These assert builder *logic* — that walls/openings/roof/slab produce the right solids
and that openings reduce volume — without the heavy CAD backend. Real-geometry and
export are exercised separately in the slow build123d kernel test.
"""

from pathlib import Path

import pytest

from ncad.build.builder import Builder
from ncad.spec.spec_loader import SpecLoader
from tests.kernel.fake_kernel import FakeKernel

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


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


def _l_spec() -> dict:
    # L footprint: 6x6 minus a 3x3 top-right notch. One wall + one room per the schema's
    # minimums; the footprint polygon is what the builder must honor for slab/roof.
    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [{"id": "w0", "start": [0, 0], "end": [6, 0], "thickness": 0.2}],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [3, 0], [3, 3], [0, 3]]}],
                "footprint": [[0, 0], [6, 0], [6, 3], [3, 3], [3, 6], [0, 6]],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_footprint_polygon_slab_excludes_notch() -> None:
    kernel = FakeKernel()

    solid = Builder(kernel).build(_l_spec())

    # The slab/roof follow the L polygon: a point in the notch (x=4.5,y=4.5) is empty,
    # both at floor level and at roof level — not filled as a bounding box would.
    assert not kernel._point_inside(solid, 4.5, 4.5, -0.1)  # floor slab
    assert not kernel._point_inside(solid, 4.5, 4.5, 3.1)  # roof slab
    # A point inside the L (the bottom-right wing) IS covered by the slab.
    assert kernel._point_inside(solid, 4.5, 1.5, -0.1)


def test_hand_authored_hocon_l_house_builds() -> None:
    # Specs originate from HOCON too: load the hand-written L house and build it.
    kernel = FakeKernel()
    spec = SpecLoader().load(str(_FIXTURES / "L_house.hocon"))

    solid = Builder(kernel).build(spec)

    assert kernel.volume(solid) > 0
    # Footprint polygon honored: the notch (top-right, x=6,y=6) is empty.
    assert not kernel._point_inside(solid, 6.0, 6.0, -0.1)


def test_export_writes_file(tmp_path) -> None:
    kernel = FakeKernel()
    out = tmp_path / "model.txt"

    builder = Builder(kernel)
    solid = builder.build(_spec())
    kernel.export(solid, str(out))

    assert out.exists()
