from ncad.viewer.spec_catalog import SpecCatalog


def _make_examples(tmp_path):
    sketching = tmp_path / "01-sketching"
    sketching.mkdir()
    (sketching / "block.hocon").write_text("x")
    other = tmp_path / "02-solid-features"
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
    assert [d["name"] for d in dirs] == ["01-sketching", "02-solid-features"]
    assert [f["name"] for f in files] == ["top.hocon"]
    section = dirs[0]
    assert section["children"][0] == {
        "type": "spec",
        "name": "block.hocon",
        "path": "01-sketching/block.hocon",
        "kind": "part",
    }


def test_tree_ignores_non_spec_files(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    names = [n["name"] for n in catalog.tree()]

    assert "notes.txt" not in names


def test_tree_of_missing_dir_is_empty(tmp_path) -> None:
    assert SpecCatalog(str(tmp_path / "nope")).tree() == []


def test_empty_dir_string_does_not_scan_cwd() -> None:
    catalog = SpecCatalog("")

    assert catalog.tree() == []
    assert catalog.resolve("anything.hocon") is None


def test_resolve_accepts_known_spec(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    resolved = catalog.resolve("01-sketching/block.hocon")

    assert resolved is not None and resolved.endswith("block.hocon")


def test_resolve_rejects_traversal(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("../secrets.hocon") is None


def test_resolve_rejects_non_spec_extension(tmp_path) -> None:
    catalog = SpecCatalog(str(_make_examples(tmp_path)))

    assert catalog.resolve("notes.txt") is None


def test_assembly_document_tagged_assembly_kind(tmp_path) -> None:
    # A .asm.hocon appears in the tree tagged kind="assembly" so the viewer filters the combobox
    # by mode and routes it to the assemble path (never the part builder).
    _make_examples(tmp_path)
    (tmp_path / "gearbox.asm.hocon").write_text("x")
    catalog = SpecCatalog(str(tmp_path))

    specs = [n for n in catalog.tree() if n["type"] == "spec"]
    asm = next(n for n in specs if n["name"] == "gearbox.asm.hocon")
    assert asm["kind"] == "assembly"
    part = next(n for n in specs if n["name"] == "top.hocon")
    assert part["kind"] == "part"
    # It resolves (it is a valid spec path), but as an assembly, not a part build.
    assert catalog.resolve("gearbox.asm.hocon") is not None


def test_motion_and_physics_documents_tagged_by_suffix(tmp_path) -> None:
    # .motion.hocon and .physics.hocon both also end in .hocon; the compound suffixes must win over
    # the bare part fallthrough so each shows in its own viewer mode's combobox.
    _make_examples(tmp_path)
    (tmp_path / "arm.motion.hocon").write_text("x")
    (tmp_path / "arm.physics.hocon").write_text("x")
    catalog = SpecCatalog(str(tmp_path))

    specs = {n["name"]: n["kind"] for n in catalog.tree() if n["type"] == "spec"}
    assert specs["arm.motion.hocon"] == "motion"
    assert specs["arm.physics.hocon"] == "physics"


def test_analysis_document_tagged_analysis_kind(tmp_path) -> None:
    # A .analysis.hocon (FEA load case) also ends in .hocon; the compound suffix must win over the
    # bare part fallthrough so it shows in the viewer's Analysis mode combobox.
    _make_examples(tmp_path)
    (tmp_path / "bracket.analysis.hocon").write_text("x")
    catalog = SpecCatalog(str(tmp_path))

    specs = {n["name"]: n["kind"] for n in catalog.tree() if n["type"] == "spec"}
    assert specs["bracket.analysis.hocon"] == "analysis"
