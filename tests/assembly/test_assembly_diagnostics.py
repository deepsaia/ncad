import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


_PARTS = """
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
"""


def test_solve_block_carries_explanation_and_roles(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
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
    solve = sidecar["solve"]
    assert "explanation" in solve and "bodies" in solve["explanation"]
    assert "redundant_ids" in solve
    m1 = next(m for m in sidecar["mates"] if m["id"] == "m1")
    assert m1["role"] in ("active", "redundant")


def test_redundant_mate_reported_not_over_constrained(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
    asm = tmp_path / "redundant.asm.hocon"
    # coincident already aligns the connector axes; adding a parallel on the SAME pair is redundant
    # (both lower to the axis-parallel primitive), not a conflict. py-slvs flags it code 5.
    _write(asm, f"""
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = plate, lock = true }}
    {{ id = pin, file = "{part.name}", part = peg }}
  ]
  constraints = [
    {{ id = m1, type = coincident, between = [
       {{ instance = base, connector = top }}, {{ instance = pin, connector = base }} ] }}
    {{ id = m2, type = parallel, between = [
       {{ instance = base, connector = top }}, {{ instance = pin, connector = base }} ] }}
  ]
}}
""")
    out = tmp_path / "out"
    AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    sidecar = json.loads((out / "redundant.assembly.json").read_text())
    assert sidecar["solve"]["status"] == "redundant"
    assert sidecar["solve"]["status"] != "over_constrained"
    assert set(sidecar["solve"]["redundant_ids"]) & {"m1", "m2"}
    # A redundant mate is still satisfied (ok) but tagged role=redundant.
    roles = {m["id"]: m["role"] for m in sidecar["mates"]}
    assert "redundant" in roles.values()
