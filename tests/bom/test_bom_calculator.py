"""Tests for BomCalculator: quantities computed from the spec, never from the mesh.

Volumes/areas are exact parametric values (length x thickness x height minus opening
volumes), per design.md §4 — so they are deterministic and golden-testable.
"""

import pytest

from ncad.bom.bom_calculator import BomCalculator


def _spec(with_opening: bool = True) -> dict:
    wall = {"id": "wall_0", "start": [0.0, 0.0], "end": [6.0, 0.0], "thickness": 0.2}
    if with_opening:
        wall["openings"] = [
            {
                "id": "door_0", "kind": "door", "along": 0.5,
                "width": 1.0, "height": 2.1, "sill": 0.0,
            },
            {
                "id": "win_0", "kind": "window", "along": 0.8,
                "width": 1.2, "height": 1.4, "sill": 0.9,
            },
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


def test_wall_gross_volume_before_openings() -> None:
    # 6m x 0.2m x 3m = 3.6 m^3
    bom = BomCalculator().quantities(_spec(with_opening=False))

    assert bom.wall_volume == pytest.approx(3.6)


def test_openings_reduce_wall_volume() -> None:
    # door 1.0x2.1, window 1.2x1.4, each x thickness 0.2
    # opening vol = (1.0*2.1 + 1.2*1.4) * 0.2 = (2.1 + 1.68) * 0.2 = 0.756
    bom = BomCalculator().quantities(_spec(with_opening=True))

    assert bom.wall_volume == pytest.approx(3.6 - 0.756)


def test_counts_doors_and_windows_by_kind() -> None:
    bom = BomCalculator().quantities(_spec(with_opening=True))

    assert bom.door_count == 1
    assert bom.window_count == 1


def test_floor_area_from_room_polygons() -> None:
    # single 6x4 room = 24 m^2
    bom = BomCalculator().quantities(_spec())

    assert bom.floor_area == pytest.approx(24.0)


def test_roof_area_covers_footprint() -> None:
    # roof covers the footprint = union of rooms; single 6x4 room = 24 m^2
    bom = BomCalculator().quantities(_spec())

    assert bom.roof_area == pytest.approx(24.0)


def test_is_deterministic() -> None:
    spec = _spec()

    assert BomCalculator().quantities(spec) == BomCalculator().quantities(spec)


def test_bom_as_dict_is_serializable() -> None:
    bom = BomCalculator().quantities(_spec())

    data = bom.as_dict()
    assert data["door_count"] == 1
    assert "wall_volume" in data


def test_multistorey_floor_sums_but_roof_is_top_only() -> None:
    # Two identical 6x4 storeys: floor_area sums both (48), roof_area = top only (24).
    storey = {
        "elevation": 0.0,
        "height": 3.0,
        "walls": [{"id": "w", "start": [0, 0], "end": [6, 0], "thickness": 0.2}],
        "rooms": [{"id": "r", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]]}],
    }
    spec = {
        "schema_version": 1,
        "seed": 1,
        "units": "m",
        "storeys": [{**storey, "elevation": 0.0}, {**storey, "elevation": 3.0}],
        "roof": {"kind": "flat", "thickness": 0.2},
    }

    bom = BomCalculator().quantities(spec)

    assert bom.floor_area == pytest.approx(48.0)
    assert bom.roof_area == pytest.approx(24.0)


def test_arc_wall_uses_arc_length_not_chord() -> None:
    import math

    # A quarter arc, radius 3: straight chord ~4.24m, but arc length = 3*(pi/2) ~ 4.71m.
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
    bom = BomCalculator().quantities(spec)

    arc_len = 3.0 * (math.pi / 2)
    # wall_volume = arc_length * height * thickness (no openings)
    assert bom.wall_volume == pytest.approx(arc_len * 3.0 * 0.2, rel=0.01)
