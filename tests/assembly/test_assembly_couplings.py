import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


_PARTS = """
schema_version = 2
units = mm
parts {
  disk { profile = solid,
    connectors = [ { id = axis, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 30 } ] }
      { id = ext, op = extrude, profile = sk, distance = 6 }
    ] }
}
"""


def test_screw_solved_and_gear_coupling_recorded(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
    asm = tmp_path / "geared.asm.hocon"
    _write(asm, f"""
schema_version = 1
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = disk, lock = true }}
    {{ id = g1, file = "{part.name}", part = disk }}
    {{ id = g2, file = "{part.name}", part = disk }}
  ]
  joints = [
    {{ id = j1, type = revolute, between = [
       {{ instance = base, connector = axis }}, {{ instance = g1, connector = axis }} ] }}
    {{ id = j2, type = revolute, between = [
       {{ instance = base, connector = axis }}, {{ instance = g2, connector = axis }} ] }}
  ]
  couplings = [
    {{ id = c1, type = gear, between = [ j1, j2 ], ratio = 2 }}
  ]
}}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "geared.assembly.json").read_text())
    couplings = sidecar["couplings"]
    assert len(couplings) == 1
    assert couplings[0]["id"] == "c1" and couplings[0]["type"] == "gear"
    assert couplings[0]["between"] == ["j1", "j2"] and couplings[0]["ratio"] == 2
    # The declared coupling is reported (not counted) in the diagnostics explanation.
    assert "declared coupling" in sidecar["solve"]["explanation"]
