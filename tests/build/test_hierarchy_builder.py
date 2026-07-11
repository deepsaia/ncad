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


def test_bodies_group_lists_per_body_material():
    # Material is a per-body property (NX/Fusion model): it shows in a Bodies group, one node
    # per body with its resolved material chip, NOT on feature/part rows.
    part = {"profile": "solid", "material": "aluminium_6061", "features": [
        {"id": "pad", "op": "extrude"},
    ]}
    bodies = [
        {"id": "pad/body/0", "material": "aluminium_6061"},
        {"id": "grp/body/1", "material": "steel_1018"},
    ]
    tree = HierarchyBuilder().hierarchy("p", part, bodies=bodies)
    # feature rows carry no material chip
    assert "material" not in tree["children"][0]
    # a Bodies group is appended after the features
    group = tree["children"][-1]
    assert group["kind"] == "group" and group["name"] == "Bodies"
    listed = [(b["id"], b["material"]) for b in group["children"]]
    assert listed == [("pad/body/0", "aluminium_6061"), ("grp/body/1", "steel_1018")]
    assert all(b["kind"] == "body" for b in group["children"])


def test_no_bodies_group_when_bodies_absent():
    tree = HierarchyBuilder().hierarchy("p", _part())
    assert all(c.get("kind") != "group" for c in tree["children"])


def test_single_body_without_material_shows_no_group_and_no_part_chip():
    # A lone contiguous body IS the part; no Bodies group, and no material authored -> no chip.
    tree = HierarchyBuilder().hierarchy("p", _part(),
                                        bodies=[{"id": "pad/body/0", "material": None}])
    assert all(c.get("kind") != "group" for c in tree["children"])
    assert "material" not in tree


def test_single_body_with_material_shows_chip_on_part_not_a_group():
    # Single body == part, so its material rides on the part row; no Bodies group.
    tree = HierarchyBuilder().hierarchy("p", _part(),
                                        bodies=[{"id": "pad/body/0", "material": "abs"}])
    assert all(c.get("kind") != "group" for c in tree["children"])
    assert tree["material"] == "abs"


def test_sketch_feature_carries_its_constraint_status():
    statuses = [SketchStatus(feature_id="sk", status="under", dof=2, failing_ids=["c1"])]
    tree = HierarchyBuilder().hierarchy("p", _part(), statuses=statuses)
    sketch_node = tree["children"][0]
    assert sketch_node["status"] == "under"
    assert sketch_node["dof"] == 2
    assert sketch_node["failing_ids"] == ["c1"]
    # a non-sketch feature carries no status
    assert "status" not in tree["children"][1]
