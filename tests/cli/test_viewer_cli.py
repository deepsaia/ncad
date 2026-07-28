from pathlib import Path

from ncad.cli.viewer_cli import ViewerCli, _issue_label


def test_default_is_out_under_project_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)

    resolved = ViewerCli().resolve_models_dir(None, start=nested)

    assert resolved == tmp_path / "out"


def test_relative_dir_resolves_against_project_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    nested = tmp_path / "src"
    nested.mkdir()

    resolved = ViewerCli().resolve_models_dir("build", start=nested)

    assert resolved == tmp_path / "build"


def test_absolute_dir_is_used_as_is(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    somewhere = tmp_path / "elsewhere"

    resolved = ViewerCli().resolve_models_dir(str(somewhere), start=tmp_path)

    assert resolved == somewhere


def test_resolve_examples_dir_is_examples_under_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "examples").mkdir()
    nested = tmp_path / "src"
    nested.mkdir()

    assert ViewerCli().resolve_examples_dir(start=nested) == tmp_path / "examples"


def test_resolve_examples_dir_none_when_absent(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")

    assert ViewerCli().resolve_examples_dir(start=tmp_path) is None


def test_issue_label_uses_whichever_id_key_is_present() -> None:
    # the crash-that-was: a joint/coupling issue has no instance_id; every id kind must render
    assert _issue_label({"instance_id": "arm", "message": "x"}) == "[arm] "
    assert _issue_label({"joint_id": "pin0", "message": "x"}) == "[pin0] "
    assert _issue_label({"coupling_id": "mesh", "message": "x"}) == "[mesh] "


def test_issue_label_empty_when_no_id() -> None:
    assert _issue_label({"message": "a plain issue"}) == ""


def test_issue_label_prefers_instance_over_joint() -> None:
    assert _issue_label({"instance_id": "a", "joint_id": "b"}) == "[a] "
