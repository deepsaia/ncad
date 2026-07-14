from ncad.assembly.connector_resolver import ConnectorResolver
from ncad.refs.element import Element


def _face_el(name, geom_type, attrs) -> Element:
    return Element(id=name, kind="face", created_by="p", tag=None, attrs=attrs, handle=object())


def test_resolves_planar_connector_to_frame() -> None:
    els = [_face_el("#face/p/aaaa", "plane",
                    {"geom_type": "plane", "type": "plane", "normal": [0, 0, 1],
                     "center": [1, 1, 5], "normal_z": 1.0, "mid_z": 5.0})]
    frames, issues = ConnectorResolver().resolve(
        [{"id": "top", "at": "select faces where normal_z > 0.9"}], els)
    assert not issues
    assert "top" in frames
    assert frames["top"].z == (0.0, 0.0, 1.0)


def _el(name, kind, attrs) -> Element:
    return Element(id=name, kind=kind, created_by="p", tag=None, attrs=attrs, handle=object())


def test_resolves_edge_connector_to_tangent_frame() -> None:
    els = [_el("#edge/p/aaaa", "edge",
               {"geom_type": "line", "type": "line", "center": [0, 0, 5],
                "edge_direction": [0, 0, 1], "length": 10.0})]
    frames, issues = ConnectorResolver().resolve(
        [{"id": "spine", "at": "select edges where type = 'line'"}], els)
    assert not issues
    assert "spine" in frames
    assert frames["spine"].z == (0.0, 0.0, 1.0)


def test_resolves_vertex_connector_to_point_frame() -> None:
    els = [_el("#vertex/p/aaaa", "vertex", {"type": "vertex", "center": [1, 2, 3]})]
    frames, issues = ConnectorResolver().resolve(
        [{"id": "corner", "at": "select vertices where type = 'vertex'"}], els)
    assert not issues
    assert frames["corner"].origin == (1.0, 2.0, 3.0)


def test_cylinder_connector_carries_radius() -> None:
    els = [_el("#face/p/aaaa", "face",
               {"geom_type": "cylinder", "type": "cylinder", "axis_location": [0, 0, 0],
                "axis_direction": [0, 0, 1], "radius": 4.0})]
    frames, issues = ConnectorResolver().resolve(
        [{"id": "bore", "at": "select faces where type = 'cylinder'"}], els)
    assert not issues
    assert frames["bore"].radius == 4.0


def test_bad_ref_is_id_attributed() -> None:
    els = []
    frames, issues = ConnectorResolver().resolve(
        [{"id": "top", "at": "select faces where normal_z > 0.9"}], els)
    assert "top" not in frames
    assert issues and issues[0]["connector_id"] == "top"
