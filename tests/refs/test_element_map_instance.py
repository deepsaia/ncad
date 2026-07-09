from ncad.refs.element import Element
from ncad.refs.element_map import ElementMap


def _face(element_id, body_id, cx):
    """A face Element created by feature 'pat' in body 'body_id', centroid x=cx."""
    attrs = {"center": (cx, 0.0, 0.0), "area": 10.0, "body_id": body_id, "created_by": "pat"}
    return Element(element_id, "face", "pat", None, attrs, object())


def _map(elements):
    m = ElementMap()
    m._elements = elements  # seed directly; rebuild is exercised elsewhere
    return m


def test_instance_resolves_by_body_ordinal_not_centroid():
    # Three instance bodies; body/2 sits at a SMALLER centroid x than body/1 on purpose,
    # so a centroid sort would disagree with the ordinal.
    elements = [
        _face("pat/face/0", "pat/body/0", cx=0.0),
        _face("pat/face/1", "pat/body/1", cx=90.0),
        _face("pat/face/2", "pat/body/2", cx=30.0),
    ]
    m = _map(elements)
    assert m.instance("pat", 0).attrs["body_id"] == "pat/body/0"
    assert m.instance("pat", 1).attrs["body_id"] == "pat/body/1"
    assert m.instance("pat", 2).attrs["body_id"] == "pat/body/2"


def test_instance_stable_under_suppression():
    # Suppress instance 1 (drop its body); 0 and 2 keep their ordinals -> no renumber.
    elements = [
        _face("pat/face/0", "pat/body/0", cx=0.0),
        _face("pat/face/2", "pat/body/2", cx=30.0),
    ]
    m = _map(elements)
    assert m.instance("pat", 0).attrs["body_id"] == "pat/body/0"
    assert m.instance("pat", 2).attrs["body_id"] == "pat/body/2"
    assert m.instance("pat", 1) is None  # gone, not silently reassigned


def test_instance_without_body_ids_falls_back_to_centroid_order():
    # No body_id -> single-body feature; old centroid-sort behavior is preserved.
    a = Element("h/face/0", "face", "h", None, {"center": (5.0, 0.0, 0.0), "area": 1.0}, object())
    b = Element("h/face/1", "face", "h", None, {"center": (1.0, 0.0, 0.0), "area": 1.0}, object())
    m = _map([a, b])
    assert m.instance("h", 0).id == "h/face/1"  # smaller centroid x sorts first
