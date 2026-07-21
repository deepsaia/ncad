"""ModelCatalog robot discovery: .robot.json names/labels + safe resolution + delete cleanup."""

import json

from ncad.viewer.model_catalog import ModelCatalog


def test_lists_robot_names(tmp_path):
    (tmp_path / "arm.robot.json").write_text(json.dumps({"joints": [{"name": "j1"}]}))
    (tmp_path / "gripper.robot.json").write_text(json.dumps({"joints": []}))
    (tmp_path / "part.glb").write_bytes(b"\x00")   # not a robot
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.robot_names() == ["arm", "gripper"]


def test_robot_label_is_joint_count(tmp_path):
    (tmp_path / "arm.robot.json").write_text(
        json.dumps({"joints": [{"name": "j1"}, {"name": "j2"}]}))
    labels = {r["name"]: r["label"] for r in ModelCatalog(str(tmp_path)).robots_with_labels()}
    assert labels["arm"] == "2j"


def test_resolve_robot_and_sweeps(tmp_path):
    (tmp_path / "arm.robot.json").write_text("{}")
    (tmp_path / "arm.robot_sweeps.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_robot("arm").endswith("arm.robot.json")
    assert catalog.resolve_robot_sweeps("arm").endswith("arm.robot_sweeps.json")
    assert catalog.resolve_robot("missing") is None


def test_resolve_robot_rejects_traversal(tmp_path):
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_robot("../evil") is None


def test_delete_assembly_removes_robot_sidecars(tmp_path):
    (tmp_path / "arm.assembly.json").write_text("{}")
    (tmp_path / "arm.robot.json").write_text("{}")
    (tmp_path / "arm.robot_sweeps.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.delete_assembly("arm") == "arm"
    assert not (tmp_path / "arm.robot.json").exists()
    assert not (tmp_path / "arm.robot_sweeps.json").exists()
