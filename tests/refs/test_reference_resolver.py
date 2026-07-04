from ncad.refs.element_map import ElementMap
from ncad.refs.reference import Reference
from ncad.refs.reference_resolver import ReferenceResolver


def _face(cx, cy, cz, area, normal=(0.0, 0.0, 1.0)):
    return {"kind": "face", "handle": object(), "geom_type": "planar", "normal": normal,
            "area": area, "center": (cx, cy, cz), "min_z": cz, "mid_z": cz, "max_z": cz}


def _map_with_pad():
    m = ElementMap()
    m.rebuild("pad", [_face(0, 0, 10, 100), _face(0, 0, 0, 100, normal=(0, 0, -1))],
              tags={0: "cap(+Z)", 1: "cap(-Z)"})
    return m


def test_semantic_feature_resolves_to_shape():
    resolver = ReferenceResolver(ElementMap())
    res = resolver.resolve(Reference.parse("sk"), {"sk": "SHAPE"}, [])
    assert res.error is None and res.shapes == ["SHAPE"]


def test_semantic_missing_feature_errors():
    resolver = ReferenceResolver(ElementMap())
    res = resolver.resolve(Reference.parse("nope"), {"sk": "SHAPE"}, [])
    assert res.error is not None and not res.shapes


def test_generative_cap_resolves_to_element():
    m = _map_with_pad()
    resolver = ReferenceResolver(m)
    res = resolver.resolve(Reference.parse("pad.cap(+Z)"), {}, m.elements())
    assert res.error is None and len(res.elements) == 1
    assert res.elements[0].tag == "cap(+Z)"


def test_selector_resolves_to_elements():
    m = _map_with_pad()
    resolver = ReferenceResolver(m)
    res = resolver.resolve(
        Reference.parse("select faces where created_by='pad'"), {}, m.elements())
    assert res.error is None and len(res.elements) == 2


def test_selector_empty_selection_is_error():
    m = _map_with_pad()
    resolver = ReferenceResolver(m)
    res = resolver.resolve(
        Reference.parse("select faces where created_by='ghost'"), {}, m.elements())
    assert res.error is not None


def test_bad_selector_returns_error_not_raise():
    m = _map_with_pad()
    resolver = ReferenceResolver(m)
    res = resolver.resolve(
        Reference.parse("select faces where convexity='x'"), {}, m.elements())
    assert res.error is not None


def test_instance_resolves():
    m = ElementMap()
    m.rebuild("holes", [_face(1, 1, 0, 5), _face(9, 9, 0, 5)], tags={})
    resolver = ReferenceResolver(m)
    res = resolver.resolve(Reference.parse("holes.instance(0)"), {}, m.elements())
    assert res.error is None and res.elements[0].attrs["center"] == (1, 1, 0)
