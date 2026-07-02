"""Tests for ModelCatalog: discovers glTF/GLB models in a directory."""

from ncad.viewer.model_catalog import ModelCatalog


def test_lists_gltf_and_glb_models(tmp_path) -> None:
    (tmp_path / "a.gltf").write_text("{}")
    (tmp_path / "b.glb").write_bytes(b"\x00")
    (tmp_path / "notes.txt").write_text("ignore me")

    catalog = ModelCatalog(str(tmp_path))
    names = catalog.model_names()

    assert names == ["a.gltf", "b.glb"]


def test_empty_directory_returns_empty_list(tmp_path) -> None:
    assert ModelCatalog(str(tmp_path)).model_names() == []


def test_missing_directory_returns_empty_list(tmp_path) -> None:
    assert ModelCatalog(str(tmp_path / "does_not_exist")).model_names() == []


def test_names_are_sorted(tmp_path) -> None:
    for name in ("zebra.gltf", "alpha.gltf", "mid.glb"):
        (tmp_path / name).write_text("{}")

    assert ModelCatalog(str(tmp_path)).model_names() == ["alpha.gltf", "mid.glb", "zebra.gltf"]


def test_resolve_path_returns_absolute_path_for_known_model(tmp_path) -> None:
    (tmp_path / "a.gltf").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))

    resolved = catalog.resolve("a.gltf")

    assert resolved is not None
    assert resolved.endswith("a.gltf")


def test_resolve_rejects_unknown_or_traversal(tmp_path) -> None:
    (tmp_path / "a.gltf").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))

    assert catalog.resolve("missing.gltf") is None
    assert catalog.resolve("../secret.gltf") is None


def test_resolve_meta_finds_sidecar(tmp_path) -> None:
    (tmp_path / "block.glb").write_bytes(b"x")
    (tmp_path / "block.meta.json").write_text("{}")
    catalog = ModelCatalog(str(tmp_path))

    resolved = catalog.resolve_meta("block.glb")

    assert resolved is not None and resolved.endswith("block.meta.json")


def test_models_with_sources_reads_source_from_meta(tmp_path) -> None:
    (tmp_path / "block.glb").write_bytes(b"x")
    (tmp_path / "block.meta.json").write_text('{"source": "examples/g/block.hocon"}')
    (tmp_path / "plain.glb").write_bytes(b"x")
    catalog = ModelCatalog(str(tmp_path))

    listed = catalog.models_with_sources()

    by_name = {m["name"]: m["source"] for m in listed}
    assert by_name == {"block.glb": "examples/g/block.hocon", "plain.glb": None}


def test_delete_model_removes_glb_and_sidecars(tmp_path) -> None:
    for suffix in (".glb", ".meta.json", ".bom.json", ".plan.svg"):
        (tmp_path / f"block{suffix}").write_text("x")
    (tmp_path / "other.glb").write_bytes(b"x")
    catalog = ModelCatalog(str(tmp_path))

    removed = catalog.delete_model("block.glb")

    assert removed is not None and len(removed) == 4
    assert not (tmp_path / "block.glb").exists()
    assert not (tmp_path / "block.meta.json").exists()
    assert (tmp_path / "other.glb").exists()


def test_delete_model_rejects_traversal(tmp_path) -> None:
    catalog = ModelCatalog(str(tmp_path))

    assert catalog.delete_model("../evil.glb") is None


def test_delete_unknown_model_returns_none(tmp_path) -> None:
    catalog = ModelCatalog(str(tmp_path))

    assert catalog.delete_model("nope.glb") is None
