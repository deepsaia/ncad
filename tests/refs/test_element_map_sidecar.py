from ncad.refs.element import Element
from ncad.refs.element_map import ElementMap


def _map(elements):
    m = ElementMap()
    m._elements = elements
    return m


def test_sidecar_includes_body_id_from_attrs():
    e = Element("pat/face/0", "face", "pat", None,
                {"body_id": "pat/body/1"}, object())
    rec = _map([e]).to_sidecar()[0]
    assert rec["body_id"] == "pat/body/1"
    assert rec["id"] == "pat/face/0" and rec["kind"] == "face"


def test_sidecar_body_id_is_none_when_absent():
    e = Element("h/face/0", "face", "h", None, {}, object())
    assert _map([e]).to_sidecar()[0]["body_id"] is None
