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
