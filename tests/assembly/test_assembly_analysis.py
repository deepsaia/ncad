import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


_PARTS = """
units = mm
parts {
  plate { profile = solid, material = steel_1018,
    connectors = [ { id = top, at = "select faces where normal_z > 0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 40, h = 40 } ] }
      { id = ext, op = extrude, profile = sk, distance = 6 }
    ] }
  peg { profile = solid, material = steel_1018,
    connectors = [ { id = base, at = "select faces where normal_z < -0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] }
      { id = ext, op = extrude, profile = sk, distance = 20 }
    ] }
}
"""


def test_assembly_writes_interference_bom_mass_and_step(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "parts.hocon"
    _write(part, _PARTS)
    asm = tmp_path / "pegged.asm.hocon"
    _write(asm, f"""
units = mm
assembly {{
  instances = [
    {{ id = base, file = "{part.name}", part = plate, lock = true }}
    {{ id = pin, file = "{part.name}", part = peg,
       connect = {{ my = base, to = {{ instance = base, connector = top }} }} }}
  ]
}}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "pegged.assembly.json").read_text())
    # Interference is checked + classified for the pair. This connect example seats the peg base on
    # the plate top so the peg dips into the plate -> a real interference with positive volume
    # (the detector correctly catches it; touching vs overlap correctness is the assembly capstone).
    pair = next(f for f in sidecar["interference"] if {f["a"], f["b"]} == {"base", "pin"})
    assert pair["status"] == "interfering" and pair["volume"] > 0
    # BOM: two distinct parts, quantity 1 each; mass roll-up present + positive.
    parts = {i["part"] for i in sidecar["bom"]["items"]}
    assert parts == {"plate", "peg"}
    assert sidecar["mass"]["total_mass"] > 0
    # Structured STEP written beside the sidecar.
    assert (out / "pegged.step").is_file()
