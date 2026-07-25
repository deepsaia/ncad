import json
from pathlib import Path

from ncad.viewer.model_catalog import ModelCatalog


def _asm(root: Path, name: str, motion: dict | None = None) -> Path:
    """Create out/assemblies/<name>/<name>.assembly.json (+ optional <name>.motion.json)."""
    d = root / "assemblies" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.assembly.json").write_text(json.dumps({"name": name, "instances": []}))
    if motion is not None:
        (d / f"{name}.motion.json").write_text(json.dumps(motion))
    return d


def test_catalog_lists_and_resolves_assembly(tmp_path: Path) -> None:
    _asm(tmp_path, "gearbox")
    catalog = ModelCatalog(str(tmp_path))
    assert "gearbox" in catalog.assembly_names()
    resolved = catalog.resolve_assembly("gearbox")
    assert resolved is not None and resolved.endswith("/assemblies/gearbox/gearbox.assembly.json")


def test_catalog_rejects_unsafe_assembly_name(tmp_path: Path) -> None:
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_assembly("../etc/passwd") is None


def test_catalog_lists_motion_names(tmp_path: Path) -> None:
    _asm(tmp_path, "crank_slider", motion={"name": "crank_slider"})
    _asm(tmp_path, "four_bar", motion={"name": "four_bar"})
    _asm(tmp_path, "static_rig")   # assembly with NO motion sidecar
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.motion_names() == ["crank_slider", "four_bar"]  # sorted, only those with motion


def test_motions_with_labels_reports_declared_value(tmp_path: Path) -> None:
    # steps declared -> "<n> steps"; fps declared -> "<n>fps"; neither -> frame count "<n>f".
    _asm(tmp_path, "cam", motion={"name": "cam", "driver": {"steps": 72}, "frames": [1] * 73})
    _asm(tmp_path, "belt",
         motion={"name": "belt", "driver": {"fps": 30, "duration": 2}, "frames": [1] * 61})
    _asm(tmp_path, "bare", motion={"name": "bare", "driver": {}, "frames": [1] * 12})
    catalog = ModelCatalog(str(tmp_path))
    labels = {m["name"]: m["label"] for m in catalog.motions_with_labels()}
    assert labels == {"cam": "72 steps", "belt": "30fps", "bare": "12f"}


def test_motions_with_labels_survives_unreadable_trajectory(tmp_path: Path) -> None:
    d = _asm(tmp_path, "broken")
    (d / "broken.motion.json").write_text("{ not valid json")
    catalog = ModelCatalog(str(tmp_path))
    entries = catalog.motions_with_labels()
    assert entries == [{"name": "broken", "label": None}]   # listed, just no label


def test_catalog_resolves_motion_sidecar(tmp_path: Path) -> None:
    _asm(tmp_path, "crank_slider", motion={"name": "crank_slider", "frames": []})
    catalog = ModelCatalog(str(tmp_path))
    resolved = catalog.resolve_motion("crank_slider")
    assert resolved is not None
    assert resolved.endswith("/assemblies/crank_slider/crank_slider.motion.json")
    assert catalog.resolve_motion("missing") is None
    assert catalog.resolve_motion("../etc/passwd") is None


def test_delete_assembly_removes_motion_sidecar(tmp_path: Path) -> None:
    d = _asm(tmp_path, "rig", motion={"name": "rig", "frames": []})
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.delete_assembly("rig") == "rig"
    assert not d.exists()   # whole assembly dir gone (motion sidecar with it)
