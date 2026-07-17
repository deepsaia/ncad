import json
from pathlib import Path

from ncad.viewer.model_catalog import ModelCatalog


def test_catalog_lists_and_resolves_assembly(tmp_path: Path) -> None:
    (tmp_path / "gearbox.assembly.json").write_text(
        json.dumps({"name": "gearbox", "instances": []}))
    (tmp_path / "widget.glb").write_bytes(b"glTF-ish")
    catalog = ModelCatalog(str(tmp_path))
    assert "gearbox" in catalog.assembly_names()
    resolved = catalog.resolve_assembly("gearbox")
    assert resolved is not None and resolved.endswith("gearbox.assembly.json")


def test_catalog_rejects_unsafe_assembly_name(tmp_path: Path) -> None:
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_assembly("../etc/passwd") is None


def test_catalog_lists_motion_names(tmp_path: Path) -> None:
    (tmp_path / "crank_slider.motion.json").write_text(json.dumps({"name": "crank_slider"}))
    (tmp_path / "four_bar.motion.json").write_text(json.dumps({"name": "four_bar"}))
    (tmp_path / "static_rig.assembly.json").write_text(json.dumps({"name": "static_rig"}))
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.motion_names() == ["crank_slider", "four_bar"]  # sorted, only motion sidecars


def test_catalog_resolves_motion_sidecar(tmp_path: Path) -> None:
    (tmp_path / "crank_slider.motion.json").write_text(
        json.dumps({"name": "crank_slider", "frames": []}))
    catalog = ModelCatalog(str(tmp_path))
    resolved = catalog.resolve_motion("crank_slider")
    assert resolved is not None and resolved.endswith("crank_slider.motion.json")
    assert catalog.resolve_motion("missing") is None
    assert catalog.resolve_motion("../etc/passwd") is None


def test_delete_assembly_removes_motion_sidecar(tmp_path: Path) -> None:
    (tmp_path / "rig.assembly.json").write_text(json.dumps({"name": "rig", "instances": []}))
    (tmp_path / "rig.motion.json").write_text(json.dumps({"name": "rig", "frames": []}))
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.delete_assembly("rig") == "rig"
    assert not (tmp_path / "rig.assembly.json").exists()
    assert not (tmp_path / "rig.motion.json").exists()
