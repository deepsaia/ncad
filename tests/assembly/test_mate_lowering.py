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


def _cyl(radius=4.0) -> ConnectorFrame:
    return ConnectorFrame.from_axis((0, 0, 0), (0, 0, 1), radius=radius)


def test_tangent_cylinder_to_plane_lowers_to_point_plane_distance() -> None:
    prims = MateLowering().lower({"id": "m", "type": "tangent"}, _cyl(4.0), _frame())
    assert any(p["kind"] == "point_plane_distance" and p["value"] == 4.0 for p in prims)


def test_tangent_without_radius_raises() -> None:
    with pytest.raises(MateError):
        MateLowering().lower({"id": "m", "type": "tangent"}, _frame(), _frame())


def test_symmetric_lowers_to_symmetric_plane_distances() -> None:
    # A at z=0, B at z=10, plane C at z=5 (normal +Z): symmetric pins both about C.
    frame_a = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    frame_b = ConnectorFrame.from_planar((0, 0, 10), (0, 0, 1))
    frame_c = ConnectorFrame.from_planar((0, 0, 5), (0, 0, 1))
    prims = MateLowering().lower(
        {"id": "m", "type": "symmetric", "_frame_c": frame_c}, frame_a, frame_b)
    kinds = [p["kind"] for p in prims]
    assert kinds == ["point_plane_distance", "point_plane_distance"]
    # A is -5 from C, B is +5 from C (mirror across C's plane).
    assert prims[0]["a"] == "A.origin" and prims[0]["b"] == "C.plane" and prims[0]["value"] == -5.0
    assert prims[1]["a"] == "B.origin" and prims[1]["b"] == "C.plane" and prims[1]["value"] == 5.0


def test_width_centers_a_between_two_planes() -> None:
    # B at z=0 and C at z=10 (both +Z): A is centered at the midplane, 5 from B.
    frame_a = ConnectorFrame.from_planar((0, 0, 3), (0, 0, 1))
    frame_b = ConnectorFrame.from_planar((0, 0, 0), (0, 0, 1))
    frame_c = ConnectorFrame.from_planar((0, 0, 10), (0, 0, 1))
    prims = MateLowering().lower(
        {"id": "m", "type": "width", "_frame_c": frame_c}, frame_a, frame_b)
    assert prims[0]["kind"] == "point_plane_distance"
    # Halfway between B (z=0) and C (z=10) is 5 from B along +Z.
    assert prims[0]["a"] == "A.origin" and prims[0]["b"] == "B.plane" and prims[0]["value"] == 5.0


def test_symmetric_without_third_ref_raises() -> None:
    with pytest.raises(MateError):
        MateLowering().lower({"id": "m", "type": "symmetric"}, _frame(), _frame())


def test_unknown_type_raises() -> None:
    with pytest.raises(MateError):
        MateLowering().lower({"id": "m", "type": "welded"}, _frame(), _frame())
