import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _write(p: Path, s: str) -> None:
    p.write_text(s)


def test_connect_snaps_instance_onto_target(tmp_path) -> None:
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    part = tmp_path / "blocks.hocon"
    _write(part, """
schema_version = 2
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
    asm = tmp_path / "stack.asm.hocon"
    _write(asm, f"""
schema_version = 1
units = mm
assembly {{ instances = [
  {{ id = base, file = "{part.name}", part = plate }}
  {{ id = pin, file = "{part.name}", part = peg,
     connect = {{ my = base, to = {{ instance = base, connector = top }} }} }}
] }}
""")
    out = tmp_path / "out"
    result = AssemblyBuilder(Build123dKernel()).assemble(str(asm), str(out))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((out / "stack.assembly.json").read_text())
    pin = next(i for i in sidecar["instances"] if i["id"] == "pin")
    # The peg's base connector snapped onto the plate top (z=6mm = 0.006m): the pin's placement
    # lifts it to sit on the plate top.
    assert pin["placement"][3][2] == pytest.approx(0.006, abs=1e-6)
    # Connector frames are emitted for the viewer overlay.
    assert any(c["id"] == "base" for c in pin["connectors"])
