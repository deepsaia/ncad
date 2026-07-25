"""Tests for ModelCatalog over the out/<kind>/<name>/ layout (a thin OutputLayout facade)."""

from pathlib import Path

from ncad.viewer.model_catalog import ModelCatalog


def _part(root: Path, stem: str, ext: str = ".glb") -> None:
    """Create out/parts/<stem>/<stem><ext>."""
    d = root / "parts" / stem
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{stem}{ext}").write_text("x")


def test_lists_gltf_and_glb_models(tmp_path) -> None:
    _part(tmp_path, "a", ".gltf")
    _part(tmp_path, "b", ".glb")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.model_names() == ["a.gltf", "b.glb"]


def test_empty_directory_returns_empty_list(tmp_path) -> None:
    assert ModelCatalog(str(tmp_path)).model_names() == []


def test_missing_directory_returns_empty_list(tmp_path) -> None:
    assert ModelCatalog(str(tmp_path / "does_not_exist")).model_names() == []


def test_names_are_sorted(tmp_path) -> None:
    _part(tmp_path, "zebra", ".gltf")
    _part(tmp_path, "alpha", ".gltf")
    _part(tmp_path, "mid", ".glb")
    assert ModelCatalog(str(tmp_path)).model_names() == ["alpha.gltf", "mid.glb", "zebra.gltf"]


def test_resolve_path_returns_absolute_path_for_known_model(tmp_path) -> None:
    _part(tmp_path, "a", ".gltf")
    resolved = ModelCatalog(str(tmp_path)).resolve("a.gltf")
    assert resolved is not None and resolved.endswith("/parts/a/a.gltf")


def test_resolve_rejects_unknown_or_traversal(tmp_path) -> None:
    _part(tmp_path, "a", ".gltf")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve("missing.gltf") is None
    assert catalog.resolve("../secret.gltf") is None


def test_resolve_meta_finds_sidecar(tmp_path) -> None:
    _part(tmp_path, "block")
    (tmp_path / "parts" / "block" / "block.meta.json").write_text("{}")
    resolved = ModelCatalog(str(tmp_path)).resolve_meta("block.glb")
    assert resolved is not None and resolved.endswith("/parts/block/block.meta.json")


def test_models_with_sources_reads_source_from_meta(tmp_path) -> None:
    _part(tmp_path, "block")
    (tmp_path / "parts" / "block" / "block.meta.json").write_text(
        '{"source": "examples/g/block.hocon"}')
    _part(tmp_path, "plain")
    by_name = {m["name"]: m["source"] for m in ModelCatalog(str(tmp_path)).models_with_sources()}
    assert by_name == {"block.glb": "examples/g/block.hocon", "plain.glb": None}


def test_delete_model_removes_the_part_dir(tmp_path) -> None:
    _part(tmp_path, "block")
    for suffix in (".meta.json", ".bom.json", ".plan.svg"):
        (tmp_path / "parts" / "block" / f"block{suffix}").write_text("x")
    _part(tmp_path, "other")
    catalog = ModelCatalog(str(tmp_path))
    removed = catalog.delete_model("block.glb")
    assert removed is not None and len(removed) == 1  # the whole dir, one entry
    assert not (tmp_path / "parts" / "block").exists()
    assert (tmp_path / "parts" / "other" / "other.glb").exists()  # neighbor untouched


def test_delete_model_rejects_traversal(tmp_path) -> None:
    # "../evil.glb" -> stem "evil" -> out/parts/evil/ which does not exist -> None (no escape).
    assert ModelCatalog(str(tmp_path)).delete_model("../evil.glb") is None


def test_delete_unknown_model_returns_none(tmp_path) -> None:
    assert ModelCatalog(str(tmp_path)).delete_model("nope.glb") is None


def test_resolve_elementmap(tmp_path) -> None:
    _part(tmp_path, "m")
    (tmp_path / "parts" / "m" / "m.elementmap.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_elementmap("m.glb") is not None
    assert catalog.resolve_elementmap("missing.glb") is None


def test_resolve_hierarchy(tmp_path) -> None:
    _part(tmp_path, "m")
    (tmp_path / "parts" / "m" / "m.hierarchy.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve_hierarchy("m.glb") is not None
    assert catalog.resolve_hierarchy("missing.glb") is None


def test_member_glb_resolves_from_assembly_dir(tmp_path) -> None:
    # A member glb lives in the assembly dir; resolve (servable) finds it by bare name.
    d = tmp_path / "assemblies" / "crank"
    d.mkdir(parents=True)
    (d / "rod.glb").write_text("x")
    (d / "crank.assembly.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.resolve("rod.glb").endswith("/assemblies/crank/rod.glb")
    assert catalog.assembly_names() == ["crank"]


def test_delete_assembly_removes_dir_with_motion(tmp_path) -> None:
    d = tmp_path / "assemblies" / "crank"
    d.mkdir(parents=True)
    (d / "crank.assembly.json").write_text("{}")
    (d / "crank.motion.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))
    assert catalog.delete_assembly("crank") == "crank"
    assert not d.exists()                      # whole dir gone (motion with it)
    assert catalog.delete_assembly("crank") is None   # idempotent
