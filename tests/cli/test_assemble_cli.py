import pytest
from typer.testing import CliRunner

from ncad.cli.viewer_cli import app

pytestmark = pytest.mark.slow

_RUNNER = CliRunner()


def test_assemble_command_builds_scene(tmp_path) -> None:
    part = tmp_path / "peg.hocon"
    part.write_text("""
schema_version = 2
units = mm
parts { peg { profile = solid, features = [
  { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] }
  { id = ext, op = extrude, profile = sk, distance = 20 }
] } }
""")
    asm = tmp_path / "pegs.asm.hocon"
    asm.write_text(f"""
schema_version = 1
units = mm
assembly {{ instances = [ {{ id = p1, file = "{part.name}", part = peg }} ] }}
""")
    out = tmp_path / "out"
    result = _RUNNER.invoke(app, ["assemble", str(asm), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert (out / "pegs.assembly.json").is_file()
