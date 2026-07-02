from pathlib import Path

import pytest

from ncad.cli.project_root import find_project_root


def test_finds_root_from_a_nested_subdirectory(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'x'\n")

    found = find_project_root(root / "src" / "pkg")

    assert found == root


def test_returns_root_itself_when_started_at_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")

    assert find_project_root(tmp_path) == tmp_path


def test_raises_when_no_pyproject_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        find_project_root(tmp_path)
