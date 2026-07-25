"""ModelCatalog robot discovery: .robot.json names/labels + safe resolution + delete cleanup."""

import json
from pathlib import Path

from ncad.viewer.model_catalog import ModelCatalog


def _robot(root: Path, name: str, tree: dict, sweeps: bool = False) -> Path:
    """Create out/robots/<name>/<name>.robot.json (+ optional sweeps)."""
    d = root / "robots" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.robot.json").write_text(json.dumps(tree))
    if sweeps:
        (d / f"{name}.robot_sweeps.json").write_text("{}")
    return d


def test_lists_robot_names(tmp_path):
    _robot(tmp_path, "arm", {"joints": [{"name": "j1"}]})
    _robot(tmp_path, "gripper", {"joints": []})
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.robot_names() == ["arm", "gripper"]


def test_robot_label_is_joint_count(tmp_path):
    _robot(tmp_path, "arm", {"joints": [{"name": "j1"}, {"name": "j2"}]})
    labels = {r["name"]: r["label"] for r in ModelCatalog(str(tmp_path)).robots_with_labels()}
    assert labels["arm"] == "2j"


def test_resolve_robot_and_sweeps(tmp_path):
    _robot(tmp_path, "arm", {}, sweeps=True)
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_robot("arm").endswith("/robots/arm/arm.robot.json")
    assert catalog.resolve_robot_sweeps("arm").endswith("/robots/arm/arm.robot_sweeps.json")
    assert catalog.resolve_robot("missing") is None


def test_resolve_robot_rejects_traversal(tmp_path):
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_robot("../evil") is None


def test_robots_with_labels_carries_source(tmp_path):
    # The list payload includes the recorded .physics.hocon source so the viewer can Regenerate.
    _robot(tmp_path, "arm", {"joints": [{"name": "j1"}], "source": "/x/arm.physics.hocon"})
    row = next(r for r in ModelCatalog(str(tmp_path)).robots_with_labels() if r["name"] == "arm")
    assert row["source"] == "/x/arm.physics.hocon"


def test_delete_robot_removes_the_robot_dir(tmp_path):
    # delete_robot drops the whole out/robots/<name>/ dir (tree + sweeps + keyframes + meshes). The
    # composed assembly (a separate out/assemblies/ dir) is a distinct kind, left untouched.
    d = _robot(tmp_path, "arm", {}, sweeps=True)
    (tmp_path / "assemblies" / "arm").mkdir(parents=True)
    (tmp_path / "assemblies" / "arm" / "arm.assembly.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.delete_robot("arm") == "arm"
    assert not d.exists()                                          # robot dir gone
    assert (tmp_path / "assemblies" / "arm" / "arm.assembly.json").exists()  # scene left in place


def test_delete_robot_unknown_returns_none(tmp_path):
    assert ModelCatalog(str(tmp_path)).delete_robot("nope") is None
