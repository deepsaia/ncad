from ncad.build.hierarchy_builder import HierarchyBuilder


def _part():
    return {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 40, "h": 40}]},
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 10},
        {"id": "rnd", "op": "fillet", "radius": 2, "edges": "vertical"},
    ]}


def test_hierarchy_lists_part_and_features_in_order():
    tree = HierarchyBuilder().hierarchy("selector_fillet", _part())

    assert tree["name"] == "selector_fillet"
    assert tree["kind"] == "part"
    ids = [c["id"] for c in tree["children"]]
    assert ids == ["sk", "pad", "rnd"]
    ops = [c["op"] for c in tree["children"]]
    assert ops == ["sketch", "extrude", "fillet"]


def test_sketch_feature_nests_its_elements():
    tree = HierarchyBuilder().hierarchy("p", _part())

    sketch_node = tree["children"][0]
    assert sketch_node["kind"] == "feature"
    assert sketch_node["children"][0]["id"] == "r"
    assert sketch_node["children"][0]["kind"] == "element"
    assert sketch_node["children"][0]["op"] == "rectangle"


def test_non_sketch_feature_has_no_children():
    tree = HierarchyBuilder().hierarchy("p", _part())

    pad_node = tree["children"][1]
    assert pad_node["children"] == []
