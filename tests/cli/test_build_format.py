"""``ncad build --format`` exposes glb/step export, matching the ``ncad-build`` convention."""

from pathlib import Path

from typer.testing import CliRunner

from ncad.cli.viewer_cli import app

_RUNNER = CliRunner()
_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "gate-0.1-first-shape"


def _first_hocon(folder: Path) -> str:
    return str(next(folder.glob("*.hocon")))


def test_build_format_step_writes_step(tmp_path: Path) -> None:
    result = _RUNNER.invoke(
        app, ["build", _first_hocon(_EXAMPLE), "--out", str(tmp_path), "--format", "step"]
    )
    assert result.exit_code == 0, result.output
    assert list(tmp_path.glob("*.step")), "expected a .step artifact"
    assert not list(tmp_path.glob("*.glb")), "step-only build should not write glb"


def test_build_format_both_comma_writes_both(tmp_path: Path) -> None:
    result = _RUNNER.invoke(
        app, ["build", _first_hocon(_EXAMPLE), "--out", str(tmp_path), "--format", "glb,step"]
    )
    assert result.exit_code == 0, result.output
    assert list(tmp_path.glob("*.glb")), "expected a .glb artifact"
    assert list(tmp_path.glob("*.step")), "expected a .step artifact"


def test_build_default_is_glb(tmp_path: Path) -> None:
    # Bare `ncad build` (no --format) must be unchanged: glb only.
    result = _RUNNER.invoke(app, ["build", _first_hocon(_EXAMPLE), "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert list(tmp_path.glob("*.glb")), "default build should write glb"
    assert not list(tmp_path.glob("*.step")), "default build should not write step"


def test_build_format_appears_in_help() -> None:
    result = _RUNNER.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.output
