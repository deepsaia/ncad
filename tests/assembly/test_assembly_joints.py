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
  bracket { profile = solid,
    connectors = [ { id = pivot, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 40 } ] }
      { id = ext, op = extrude, profile = sk, distance = 6 }
    ] }
  lever { profile = solid,
    connectors = [ { id = hub, at = "select faces where type = 'cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 12 } ] }
      { id = ext, op = extrude, profile = sk, distance = 25 }
    ] }
}
"""


def test_revolute_joint_solves_and_records_signature(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
    asm = tmp_path / "pinned.asm.hocon"
    _write(asm, f"""
schema_version = 1
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = bracket, lock = true }}
    {{ id = arm, file = "{part.name}", part = lever }}
  ]
  joints = [
    {{ id = j1, type = revolute, between = [
       {{ instance = base, connector = pivot }}, {{ instance = arm, connector = hub }} ] }}
  ]
}}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "pinned.assembly.json").read_text())
    joints = sidecar["joints"]
    assert len(joints) == 1
    j = joints[0]
    assert j["id"] == "j1" and j["type"] == "revolute"
    # The declared signature is authoritative for "leaves 1 rotational DoF"; the solver dof is a
    # gauge-sensitive cross-check (not asserted here).
    assert j["signature"] == [{"motion": "rotation", "axis": "Z"}]
    assert j["ok"] is True
