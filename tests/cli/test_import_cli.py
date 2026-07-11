from pathlib import Path

import pytest
from typer.testing import CliRunner

from ncad.cli.viewer_cli import app

pytestmark = pytest.mark.slow

_RUNNER = CliRunner()
_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "gate-0.1-first-shape"


def _first_hocon(folder: Path) -> str:
    return str(next(folder.glob("*.hocon")))


def test_build_step_then_import_round_trips(tmp_path: Path) -> None:
    # Export a known part to STEP, then import that STEP back through ncad.
    built = _RUNNER.invoke(
        app, ["build", _first_hocon(_EXAMPLE), "--out", str(tmp_path), "--format", "step"])
    assert built.exit_code == 0, built.output
    step = next(tmp_path.glob("*.step"))
    imported = _RUNNER.invoke(app, ["import", str(step), "--out", str(tmp_path)])
    assert imported.exit_code == 0, imported.output
    assert list(tmp_path.glob("imported*.glb")) or "imported" in imported.output
