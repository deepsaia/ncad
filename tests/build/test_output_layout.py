from pathlib import Path

from ncad.build.output_layout import OutputLayout


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x")


def test_dir_for_each_kind(tmp_path):
    layout = OutputLayout(str(tmp_path))
    assert layout.dir_for("parts", "block") == tmp_path / "parts" / "block"
    assert layout.dir_for("assemblies", "crank") == tmp_path / "assemblies" / "crank"
    assert layout.dir_for("robots", "arm") == tmp_path / "robots" / "arm"
    assert layout.dir_for("analyses", "rod") == tmp_path / "analyses" / "rod"


def test_names_lists_subdirs_and_skips_dotdirs(tmp_path):
    (tmp_path / "parts" / "block").mkdir(parents=True)
    (tmp_path / "parts" / "widget").mkdir(parents=True)
    (tmp_path / "parts" / ".scratch").mkdir(parents=True)
    layout = OutputLayout(str(tmp_path))
    assert layout.names("parts") == ["block", "widget"]


def test_names_absent_kind_is_empty(tmp_path):
    assert OutputLayout(str(tmp_path)).names("robots") == []


def test_resolve_present_file(tmp_path):
    _touch(tmp_path / "parts" / "block" / "block.glb")
    layout = OutputLayout(str(tmp_path))
    resolved = layout.resolve("parts", "block", "block.glb")
    assert resolved is not None and resolved.endswith("/parts/block/block.glb")


def test_resolve_absent_file_is_none(tmp_path):
    (tmp_path / "parts" / "block").mkdir(parents=True)
    assert OutputLayout(str(tmp_path)).resolve("parts", "block", "nope.glb") is None


def test_resolve_rejects_traversal(tmp_path):
    _touch(tmp_path / "secret.txt")
    layout = OutputLayout(str(tmp_path))
    assert layout.resolve("parts", "block", "../../secret.txt") is None
    assert layout.resolve("parts", "..", "block.glb") is None
    assert layout.resolve("parts", "block", "/etc/passwd") is None


def test_servable_finds_part_and_member(tmp_path):
    _touch(tmp_path / "parts" / "block" / "block.glb")
    _touch(tmp_path / "assemblies" / "crank" / "rod.glb")
    layout = OutputLayout(str(tmp_path))
    assert layout.servable("block.glb").endswith("/parts/block/block.glb")
    assert layout.servable("rod.glb").endswith("/assemblies/crank/rod.glb")


def test_servable_unknown_and_traversal(tmp_path):
    layout = OutputLayout(str(tmp_path))
    assert layout.servable("missing.glb") is None
    assert layout.servable("../secret.txt") is None
