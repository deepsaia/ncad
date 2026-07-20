import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


def test_concentric_coincident_solves_and_records_mates(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, """
units = mm
parts {
  plate { profile = solid,
    connectors = [ { id = top, at = "select faces where normal_z > 0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 40, h = 40 } ] }
      { id = ext, op = extrude, profile = sk, distance = 6 }
    ] }
  peg { profile = solid,
    connectors = [ { id = base, at = "select faces where normal_z < -0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] }
      { id = ext, op = extrude, profile = sk, distance = 20 }
    ] }
}
""")
    asm = tmp_path / "mated.asm.hocon"
    _write(asm, f"""
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = plate, lock = true }}
    {{ id = pin, file = "{part.name}", part = peg }}
  ]
  constraints = [
    {{ id = m1, type = coincident, between = [
       {{ instance = base, connector = top }},
       {{ instance = pin, connector = base }} ] }}
  ]
}}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "mated.assembly.json").read_text())
    assert sidecar["solve"]["status"] in ("well_constrained", "under_constrained", "redundant")
    assert not sidecar["solve"]["failing_ids"]
    mate = next(m for m in sidecar["mates"] if m["id"] == "m1")
    assert mate["type"] == "coincident" and mate["ok"] is True
    # pin's base connector coincides with plate top (z=6mm=0.006m): pin origin lands on the top.
    pin = next(i for i in sidecar["instances"] if i["id"] == "pin")
    assert pin["placement"][3][2] == pytest.approx(0.006, abs=1e-4)
