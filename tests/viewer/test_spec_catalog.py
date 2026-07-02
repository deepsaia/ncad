from ncad.viewer.spec_catalog import SpecCatalog


def _make_examples(tmp_path):
    gate = tmp_path / "gate-0.1-first-shape"
    gate.mkdir()
    (gate / "block.hocon").write_text("x")
    other = tmp_path / "gate-0.2-bracket"
    other.mkdir()
    (other / "bracket.hocon").write_text("x")
    (tmp_path / "top.hocon").write_text("x")
    (tmp_path / "notes.txt").write_text("ignore me")
    return tmp_path


def test_tree_reflects_directory_structure(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    tree = catalog.tree()

    dirs = [n for n in tree if n["type"] == "dir"]
    files = [n for n in tree if n["type"] == "spec"]
    assert [d["name"] for d in dirs] == ["gate-0.1-first-shape", "gate-0.2-bracket"]
    assert [f["name"] for f in files] == ["top.hocon"]
    gate = dirs[0]
    assert gate["children"][0] == {
        "type": "spec",
        "name": "block.hocon",
        "path": "gate-0.1-first-shape/block.hocon",
    }


def test_tree_ignores_non_spec_files(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    names = [n["name"] for n in catalog.tree()]

    assert "notes.txt" not in names


def test_tree_of_missing_dir_is_empty(tmp_path) -> None:
    assert SpecCatalog(str(tmp_path / "nope")).tree() == []


def test_resolve_accepts_known_spec(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    resolved = catalog.resolve("gate-0.1-first-shape/block.hocon")

    assert resolved is not None and resolved.endswith("block.hocon")


def test_resolve_rejects_traversal(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("../secrets.hocon") is None


def test_resolve_rejects_non_spec_extension(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("notes.txt") is None
