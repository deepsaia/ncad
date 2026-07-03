from ncad.refs.element_map import ElementMap


def _face(cx, cy, cz, area, order=None):
    d = {"kind": "face", "handle": object(), "geom_type": "planar",
         "normal": (0.0, 0.0, 1.0), "area": area,
         "center": (cx, cy, cz), "min_z": cz, "mid_z": cz, "max_z": cz}
    if order is not None:
        d["order"] = order
    return d


def test_deterministic_namespaced_ids():
    m = ElementMap()
    faces = [_face(0, 0, 5, 100), _face(10, 0, 5, 100)]
    m.rebuild("pad", faces, tags={})
    ids = sorted(e.id for e in m.by_feature("pad"))
    assert ids == ["pad/face/0", "pad/face/1"]


def test_generative_tag_becomes_role():
    m = ElementMap()
    faces = [_face(0, 0, 10, 100), _face(0, 0, 0, 100)]
    m.rebuild("pad", faces, tags={0: "cap(+Z)", 1: "cap(-Z)"})
    assert m.by_tag("cap(+Z)")[0].id == "pad/cap(+Z)/0"
    assert m.by_tag("cap(-Z)")[0].id == "pad/cap(-Z)/0"


def test_instance_indexing_by_authored_order():
    m = ElementMap()
    faces = [_face(9, 9, 0, 5, order=1), _face(1, 1, 0, 5, order=0)]
    m.rebuild("holes", faces, tags={})
    assert m.instance("holes", 0).attrs["center"] == (1, 1, 0)
    assert m.instance("holes", 1).attrs["center"] == (9, 9, 0)


def test_geometric_tiebreak_when_no_order():
    m = ElementMap()
    faces = [_face(5, 0, 0, 5), _face(0, 0, 0, 5)]
    m.rebuild("f", faces, tags={})
    assert m.instance("f", 0).attrs["center"] == (0, 0, 0)


def test_provenance_carries_forward_on_match():
    m = ElementMap()
    m.rebuild("pad", [_face(0, 0, 5, 100)], tags={})
    original_id = m.by_feature("pad")[0].id
    m.rebuild("hole", [_face(0, 0, 5, 100), _face(2, 2, 2, 9)], tags={})
    survived = [e for e in m.elements() if e.attrs["center"] == (0, 0, 5)][0]
    created = [e for e in m.elements() if e.attrs["center"] == (2, 2, 2)][0]
    assert survived.created_by == "pad" and survived.id == original_id
    assert created.created_by == "hole"


def test_attrs_include_normal_components_and_orientation():
    m = ElementMap()
    m.rebuild("pad", [_face(0, 0, 5, 100)], tags={})
    e = m.by_feature("pad")[0]
    assert e.attrs["normal_z"] == 1.0
    assert e.attrs["created_by"] == "pad"
