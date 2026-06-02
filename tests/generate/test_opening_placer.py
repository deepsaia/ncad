"""Tests for the deterministic opening placer (doors + windows)."""

from ncad.generate.opening_placer import OpeningPlacer


def _wall(wall_id: str, start, end) -> dict:
    return {"id": wall_id, "start": start, "end": end, "thickness": 0.2}


def _spans_overlap(a: dict, b: dict, length: float) -> bool:
    a_lo = a["along"] * length - a["width"] / 2
    a_hi = a["along"] * length + a["width"] / 2
    b_lo = b["along"] * length - b["width"] / 2
    b_hi = b["along"] * length + b["width"] / 2
    return a_lo < b_hi and b_lo < a_hi


def test_front_door_does_not_overlap_any_window() -> None:
    # Regression: seed-7's 16m south wall put the front door span [1.90,2.90] under the
    # first window span [2.60,3.80]. The placer must keep doors and windows disjoint.
    wall = _wall("ext_south", [0.0, 0.0], [16.0, 0.0])
    length = 16.0

    result = OpeningPlacer(window_spacing=3.5).place(exterior_walls=[wall], interior_walls=[])

    openings = result["ext_south"]
    doors = [o for o in openings if o["kind"] == "door"]
    windows = [o for o in openings if o["kind"] == "window"]
    for door in doors:
        for window in windows:
            assert not _spans_overlap(door, window, length), (
                f"door {door['id']} overlaps window {window['id']}"
            )


def test_interior_wall_gets_one_centered_door() -> None:
    interior = [_wall("interior_0", [5.0, 0.0], [5.0, 6.0])]
    placer = OpeningPlacer()

    result = placer.place(exterior_walls=[], interior_walls=interior)

    openings = result["interior_0"]
    assert len(openings) == 1
    assert openings[0]["kind"] == "door"
    assert openings[0]["along"] == 0.5


def test_each_interior_wall_door_has_unique_stable_id() -> None:
    interior = [
        _wall("interior_0", [5.0, 0.0], [5.0, 6.0]),
        _wall("interior_1", [0.0, 3.0], [5.0, 3.0]),
    ]

    result = OpeningPlacer().place(exterior_walls=[], interior_walls=interior)

    ids = [o["id"] for openings in result.values() for o in openings]
    assert len(ids) == len(set(ids))
    assert all(an_id.startswith("interior_") for an_id in ids)


def test_exterior_wall_gets_windows_by_spacing() -> None:
    # 12m wall, spacing 4m -> 3 windows.
    exterior = [_wall("ext_south", [0.0, 0.0], [12.0, 0.0])]
    placer = OpeningPlacer(window_spacing=4.0)

    result = placer.place(exterior_walls=exterior, interior_walls=[])

    windows = [o for o in result["ext_south"] if o["kind"] == "window"]
    assert len(windows) == 3
    for window in windows:
        assert 0.0 < window["along"] < 1.0
        assert window["sill"] > 0.0


def test_exactly_one_front_door_across_exterior_walls() -> None:
    exterior = [
        _wall("ext_south", [0.0, 0.0], [12.0, 0.0]),
        _wall("ext_north", [12.0, 9.0], [0.0, 9.0]),
    ]

    result = OpeningPlacer(window_spacing=4.0).place(exterior_walls=exterior, interior_walls=[])

    doors = [o for ops in result.values() for o in ops if o["kind"] == "door"]
    assert len(doors) == 1
    assert doors[0]["sill"] == 0.0


def test_short_exterior_wall_gets_no_windows() -> None:
    exterior = [_wall("ext_tiny", [0.0, 0.0], [2.0, 0.0])]

    result = OpeningPlacer(window_spacing=4.0).place(exterior_walls=exterior, interior_walls=[])

    windows = [o for o in result.get("ext_tiny", []) if o["kind"] == "window"]
    assert windows == []


def test_is_deterministic() -> None:
    exterior = [_wall("ext_south", [0.0, 0.0], [12.0, 0.0])]
    interior = [_wall("interior_0", [5.0, 0.0], [5.0, 6.0])]

    a = OpeningPlacer().place(exterior_walls=exterior, interior_walls=interior)
    b = OpeningPlacer().place(exterior_walls=exterior, interior_walls=interior)

    assert a == b
