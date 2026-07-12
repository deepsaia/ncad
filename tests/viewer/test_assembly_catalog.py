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
