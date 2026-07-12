import pytest

from ncad.assembly.connector_frame import ConnectorFrame
from ncad.assembly.mate_lowering import MateError, MateLowering


def _frame() -> ConnectorFrame:
    return ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))


def test_coincident_lowers_to_points_coincident_plus_anti_parallel() -> None:
    prims = MateLowering().lower({"id": "m1", "type": "coincident"}, _frame(), _frame())
    kinds = [p["kind"] for p in prims]
    assert kinds == ["points_coincident", "anti_parallel_dirs"]
    assert prims[0]["a"] == "A.origin" and prims[0]["b"] == "B.origin"
    assert prims[1]["a"] == "A.axis" and prims[1]["b"] == "B.axis"


def test_coincident_flip_uses_parallel() -> None:
    mate = {"id": "m1", "type": "coincident", "flip": True}
    prims = MateLowering().lower(mate, _frame(), _frame())
    assert [p["kind"] for p in prims] == ["points_coincident", "parallel_dirs"]


def test_flush_lowers_to_point_in_plane_plus_parallel() -> None:
    prims = MateLowering().lower({"id": "m1", "type": "flush"}, _frame(), _frame())
    assert [p["kind"] for p in prims] == ["point_in_plane", "parallel_dirs"]
    assert prims[0]["a"] == "A.origin" and prims[0]["b"] == "B.plane"


def test_align_is_flush_synonym() -> None:
    prims = MateLowering().lower({"id": "m", "type": "align"}, _frame(), _frame())
    assert [p["kind"] for p in prims] == ["point_in_plane", "parallel_dirs"]


def test_concentric_lowers_to_axes_coincident() -> None:
    prims = MateLowering().lower({"id": "m1", "type": "concentric"}, _frame(), _frame())
    assert [p["kind"] for p in prims] == ["axes_coincident"]


def test_parallel_and_perpendicular() -> None:
    par = MateLowering().lower({"id": "m", "type": "parallel"}, _frame(), _frame())[0]
    assert par["kind"] == "parallel_dirs"
    perp = MateLowering().lower({"id": "m", "type": "perpendicular"}, _frame(), _frame())[0]
    assert perp["kind"] == "dirs_angle" and perp["value"] == 90.0


def test_angle_carries_value() -> None:
    prim = MateLowering().lower({"id": "m", "type": "angle", "value": 30}, _frame(), _frame())[0]
    assert prim["kind"] == "dirs_angle" and prim["value"] == 30.0


def test_distance_and_offset_lower_to_point_plane_distance() -> None:
    for t in ("distance", "offset"):
        prim = MateLowering().lower({"id": "m", "type": t, "value": 5}, _frame(), _frame())[0]
        assert prim["kind"] == "point_plane_distance" and prim["value"] == 5.0


def test_lock_lowers_to_lock_no_b() -> None:
    prims = MateLowering().lower({"id": "m", "type": "lock"}, _frame(), None)
    assert prims == [{"kind": "lock", "a": "A", "b": None, "value": None}]


def test_mate_synonym_of_coincident() -> None:
    prims = MateLowering().lower({"id": "m", "type": "mate"}, _frame(), _frame())
    assert [p["kind"] for p in prims] == ["points_coincident", "anti_parallel_dirs"]


def test_unknown_type_raises() -> None:
    with pytest.raises(MateError):
        MateLowering().lower({"id": "m", "type": "welded"}, _frame(), _frame())
