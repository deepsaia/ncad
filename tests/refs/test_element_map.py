from ncad.refs.element_map import ElementMap


def _face(cx, cy, cz, area, order=None):
    d = {"kind": "face", "handle": object(), "geom_type": "plane",
         "normal": (0.0, 0.0, 1.0), "area": area,
         "center": (cx, cy, cz), "min_z": cz, "mid_z": cz, "max_z": cz}
    if order is not None:
        d["order"] = order
    return d


def test_deterministic_namespaced_ids():
    # Bucket 4.1: ids are persistent names (#kind/owner/hash8), deterministic and unique.
    faces = [_face(0, 0, 5, 100), _face(10, 0, 5, 100)]
    first = ElementMap()
    first.rebuild("pad", faces, tags={})
    second = ElementMap()
    second.rebuild("pad", faces, tags={})
    ids = [e.id for e in first.by_feature("pad")]
    assert [e.id for e in second.by_feature("pad")] == ids  # deterministic
    assert len(set(ids)) == len(ids)  # unique
    assert all(i.startswith("#face/pad/") and len(i.rsplit("/", 1)[1]) == 8 for i in ids)


def test_generative_tag_becomes_role():
    # The tag still rides on the element; the id is a persistent name owned by the feature.
    m = ElementMap()
    faces = [_face(0, 0, 10, 100), _face(0, 0, 0, 100)]
    m.rebuild("pad", faces, tags={0: "cap(+Z)", 1: "cap(-Z)"})
    assert m.by_tag("cap(+Z)")[0].id.startswith("#face/pad/")
    assert m.by_tag("cap(-Z)")[0].id.startswith("#face/pad/")
    assert m.by_tag("cap(+Z)")[0].tag == "cap(+Z)"


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


def test_many_elements_get_unique_persistent_names():
    # Bucket 4.1: no more index padding; each element gets a unique #kind/owner/hash8 name.
    m = ElementMap()
    edges = [{"kind": "edge", "handle": object(), "geom_type": "line", "length": 1.0,
              "center": (float(i), 0.0, 0.0), "min_z": 0.0, "mid_z": 0.0, "max_z": 0.0}
             for i in range(12)]
    m.rebuild("f", edges, tags={})
    edge_ids = [e.id for e in m.by_feature("f")]
    assert len(set(edge_ids)) == 12
    assert all(i.startswith("#edge/f/") for i in edge_ids)
