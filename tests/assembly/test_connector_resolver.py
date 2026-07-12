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


def test_bad_ref_is_id_attributed() -> None:
    els = []
    frames, issues = ConnectorResolver().resolve(
        [{"id": "top", "at": "select faces where normal_z > 0.9"}], els)
    assert "top" not in frames
    assert issues and issues[0]["connector_id"] == "top"
