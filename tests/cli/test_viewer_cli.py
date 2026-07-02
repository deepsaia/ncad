from pathlib import Path

from ncad.cli.viewer_cli import resolve_models_dir


def test_default_is_out_under_project_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)

    resolved = resolve_models_dir(None, start=nested)

    assert resolved == tmp_path / "out"


def test_relative_dir_resolves_against_project_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    nested = tmp_path / "src"
    nested.mkdir()

    resolved = resolve_models_dir("build", start=nested)

    assert resolved == tmp_path / "build"


def test_absolute_dir_is_used_as_is(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    somewhere = tmp_path / "elsewhere"

    resolved = resolve_models_dir(str(somewhere), start=tmp_path)

    assert resolved == somewhere
