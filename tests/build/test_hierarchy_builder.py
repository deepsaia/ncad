from ncad.build.hierarchy_builder import HierarchyBuilder
from ncad.ops.sketch_status import SketchStatus


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


def test_part_and_feature_carry_material_when_present():
    part = {"profile": "solid", "material": "aluminium_6061", "features": [
        {"id": "pad", "op": "extrude", "material": "steel_1018"},
        {"id": "rnd", "op": "fillet"},
    ]}
    tree = HierarchyBuilder().hierarchy("p", part)
    assert tree["material"] == "aluminium_6061"
    assert tree["children"][0]["material"] == "steel_1018"  # feature override shown
    assert "material" not in tree["children"][1]  # no material -> no chip


def test_sketch_feature_carries_its_constraint_status():
    statuses = [SketchStatus(feature_id="sk", status="under", dof=2, failing_ids=["c1"])]
    tree = HierarchyBuilder().hierarchy("p", _part(), statuses=statuses)
    sketch_node = tree["children"][0]
    assert sketch_node["status"] == "under"
    assert sketch_node["dof"] == 2
    assert sketch_node["failing_ids"] == ["c1"]
    # a non-sketch feature carries no status
    assert "status" not in tree["children"][1]
