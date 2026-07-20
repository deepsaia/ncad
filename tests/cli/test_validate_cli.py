from typer.testing import CliRunner

from ncad.cli.viewer_cli import app

_RUNNER = CliRunner()


def test_validate_ok_exits_zero(tmp_path) -> None:
    doc = tmp_path / "block.hocon"
    doc.write_text("""
units = mm
parts { block { profile = solid, features = [
  { id = sk, op = sketch, plane = XY, elements = [ { id = r, type = rectangle, w = 10, h = 10 } ] }
  { id = pad, op = extrude, profile = sk, distance = 5 }
] } }
""")
    result = _RUNNER.invoke(app, ["validate", str(doc)])
    assert result.exit_code == 0, result.output
    assert "ok" in result.output.lower()


def test_validate_bad_part_exits_nonzero(tmp_path) -> None:
    doc = tmp_path / "bad.hocon"
    doc.write_text("parts { }\n")   # missing required 'units'
    result = _RUNNER.invoke(app, ["validate", str(doc)])
    assert result.exit_code == 1
    assert "schema" in result.output.lower()


def test_validate_assembly_bad_connector(tmp_path) -> None:
    (tmp_path / "p.hocon").write_text("""
units = mm
parts { arm {
  profile = solid
  connectors = [ { id = tip, at_point = [0,0,0], axis = [0,0,1] } ]
  features = [ { id = b, op = primitive, kind = box, w = 10, d = 10, h = 10 } ]
} }
""")
    asm = tmp_path / "a.asm.hocon"
    asm.write_text("""
units = mm
assembly {
  instances = [ { id = a, file = "p.hocon", part = arm } ]
  joints = [ { id = j, type = revolute, between = [
    { instance = a, connector = wrong }, { instance = a, connector = tip } ] } ]
}
""")
    result = _RUNNER.invoke(app, ["validate", str(asm)])
    assert result.exit_code == 1
    assert "connector" in result.output.lower()
