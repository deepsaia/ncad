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


def test_single_storey_geometry_is_byte_stable() -> None:
    # Frozen baseline captured before the multi-storey refactor. A single-storey build
    # MUST keep this exact volume + bbox (no breaking change to existing buildings).
    kernel = FakeKernel()

    solid = Builder(kernel).build(_spec())

    assert kernel.volume(solid) == pytest.approx(3.672, abs=1e-6)
    (minx, miny, minz), (maxx, maxy, maxz) = kernel.bounding_box(solid)
    assert (minx, miny, minz) == pytest.approx((0.0, -0.1, -0.2))
    assert (maxx, maxy, maxz) == pytest.approx((6.0, 0.1, 3.2))


def _two_storey_spec() -> dict:
    def storey(elevation: float) -> dict:
        return {
            "elevation": elevation,
            "height": 3.0,
            "walls": [
                {"id": "s", "start": [0, 0], "end": [6, 0], "thickness": 0.2},
                {"id": "e", "start": [6, 0], "end": [6, 4], "thickness": 0.2},
                {"id": "n", "start": [6, 4], "end": [0, 4], "thickness": 0.2},
                {"id": "w", "start": [0, 4], "end": [0, 0], "thickness": 0.2},
            ],
            "rooms": [{"id": "r", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
            "footprint": [[0, 0], [6, 0], [6, 4], [0, 4]],
        }

    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [storey(0.0), storey(3.0)],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_two_storey_stacks_to_full_height() -> None:
    kernel = FakeKernel()

    solid = Builder(kernel).build(_two_storey_spec())

    # Two 3m storeys + roof slab → top ≈ 6.2m; floor base at -0.2m.
    (_, _, minz), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz == pytest.approx(6.2, rel=0.02)
    assert minz == pytest.approx(-0.2, abs=1e-6)


def test_intermediate_storey_has_ceiling_slab() -> None:
    kernel = FakeKernel()

    solid = Builder(kernel).build(_two_storey_spec())

    # A point at the slab between storeys (z just below 3.0, inside footprint) is solid.
    assert kernel._point_inside(solid, 3.0, 2.0, 2.95)


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
    spec["roof"]["kind"] = "vault"  # not a known roof kind

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


def _rect_footprint_spec(roof_kind: str) -> dict:
    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [{"id": "w0", "start": [0, 0], "end": [8, 0], "thickness": 0.2}],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [8, 0], [8, 6], [0, 6]]}],
                "footprint": [[0, 0], [8, 0], [8, 6], [0, 6]],
            }
        ],
        "roof": {"kind": roof_kind, "thickness": 0.2, "pitch": 0.5},
    }


def test_gable_roof_over_rect_footprint_builds() -> None:
    # A pitched roof over a rectangular footprint must build (routed to ROOF_BUILDERS).
    kernel = FakeKernel()

    solid = Builder(kernel).build(_rect_footprint_spec("gable"))

    assert kernel.volume(solid) > 0
    # Apex rises above the flat wall top (storey 3.0 + slab).
    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz > 3.5


def test_hip_roof_over_rect_builds_and_rises() -> None:
    kernel = FakeKernel()
    spec = _rect_footprint_spec("hip")

    solid = Builder(kernel).build(spec)

    assert kernel.volume(solid) > 0
    (_, _, _), (_, _, maxz) = kernel.bounding_box(solid)
    assert maxz > 3.5  # hip apex above wall top


def test_hip_roof_over_l_footprint_raises() -> None:
    kernel = FakeKernel()
    spec = _l_spec()
    spec["roof"] = {"kind": "hip", "pitch": 0.5}

    with pytest.raises(ValueError, match="roof"):
        Builder(kernel).build(spec)


def test_pitched_roof_over_nonrect_footprint_still_raises() -> None:
    # L footprint + gable is genuinely deferred (needs straight skeleton).
    kernel = FakeKernel()
    spec = _l_spec()
    spec["roof"] = {"kind": "gable", "thickness": 0.2, "pitch": 0.5}

    with pytest.raises(ValueError, match="roof"):
        Builder(kernel).build(spec)


def test_footprint_polygon_slab_excludes_notch() -> None:
    kernel = FakeKernel()

    solid = Builder(kernel).build(_l_spec())

    # The slab/roof follow the L polygon: a point in the notch (x=4.5,y=4.5) is empty,
    # both at floor level and at roof level — not filled as a bounding box would.
    assert not kernel._point_inside(solid, 4.5, 4.5, -0.1)  # floor slab
    assert not kernel._point_inside(solid, 4.5, 4.5, 3.1)  # roof slab
    # A point inside the L (the bottom-right wing) IS covered by the slab.
    assert kernel._point_inside(solid, 4.5, 1.5, -0.1)


def _rounded_rect_spec(radius: float) -> dict:
    # A rectangular footprint where one corner (index 2 = (6,4)) is rounded.
    corner = {"point": [6, 4], "corner_radius": radius} if radius > 0 else [6, 4]
    return {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [{"id": "w0", "start": [0, 0], "end": [6, 0], "thickness": 0.2}],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
                "footprint": [[0, 0], [6, 0], corner, [0, 4]],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }


def test_rounded_corner_slab_is_smaller_than_sharp() -> None:
    kernel = FakeKernel()

    sharp = kernel.volume(Builder(kernel).build(_rounded_rect_spec(0.0)))
    rounded = kernel.volume(Builder(kernel).build(_rounded_rect_spec(1.5)))

    assert rounded < sharp  # the fillet removes slab + roof corner material


def test_plain_footprint_builds_same_with_or_without_zero_radius() -> None:
    # A footprint of all-plain points must build identically (dispatch must not change it).
    kernel = FakeKernel()
    spec_plain = _rounded_rect_spec(0.0)

    solid = Builder(kernel).build(spec_plain)

    assert kernel.volume(solid) > 0
    # Notch-free rectangle: a deep-interior point is solid.
    assert kernel._point_inside(solid, 3.0, 2.0, -0.1)


def test_diagonal_straight_wall_builds() -> None:
    # A non-axis-aligned straight wall must build (oriented rectangle), not raise.
    kernel = FakeKernel()
    spec = {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [
                    {"id": "diag", "start": [0.0, 0.0], "end": [4.0, 3.0], "thickness": 0.2}
                ],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [4, 0], [4, 3], [0, 3]]}],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }

    solid = Builder(kernel).build(spec)

    assert kernel.volume(solid) > 0


def test_arc_wall_builds_with_positive_volume() -> None:
    kernel = FakeKernel()
    spec = {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [
            {
                "elevation": 0.0,
                "height": 3.0,
                "walls": [
                    {
                        "id": "arc_0",
                        "start": [3.0, 0.0],
                        "end": [0.0, 3.0],
                        "thickness": 0.2,
                        "arc": {"center": [0.0, 0.0], "clockwise": False},
                    }
                ],
                "rooms": [{"id": "r0", "polygon": [[0, 0], [3, 0], [3, 3], [0, 3]]}],
            }
        ],
        "roof": {"kind": "flat", "thickness": 0.2},
    }

    solid = Builder(kernel).build(spec)

    assert kernel.volume(solid) > 0


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
