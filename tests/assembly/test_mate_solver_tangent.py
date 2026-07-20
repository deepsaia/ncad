import json
import os

import pytest

pytestmark = pytest.mark.slow

_PART = '''units = mm
parts {
  pin { profile = solid,
    connectors = [ { id = shaft, at = "select faces where type='cylinder'" } ],
    features = [
      { id = sk, op = sketch, plane = XY, elements = [ { id = c, type = circle, d = 8 } ] },
      { id = ext, op = extrude, profile = sk, distance = 20 } ] }
  plate { profile = solid,
    connectors = [ { id = face, at = "select faces where type='plane' and normal_z>0.9" } ],
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 40, h = 40 } ] },
      { id = ext, op = extrude, profile = sk, distance = 4 } ] }
}'''

_ASM = '''units = mm
assembly {
  instances = [
    { id = base, file = "p.hocon", part = plate, lock = true }
    { id = shaft, file = "p.hocon", part = pin }
  ]
  constraints = [
    { id = t1, type = tangent, between = [
      { instance = shaft, connector = shaft }, { instance = base, connector = face } ] }
  ]
}'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_tangent_mate_solves(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    asm = _write(str(tmp_path), "a.asm.hocon", _ASM)
    result = AssemblyBuilder(Build123dKernel()).assemble(asm, str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "a.assembly.json").read_text())
    # The tangent mate is active (a distance constraint; the pin is otherwise free to slide/spin,
    # so the network may be under-constrained, which is fine).
    t = next(m for m in sidecar["mates"] if m["id"] == "t1")
    assert t["ok"]
    assert sidecar["solve"]["status"] in ("well_constrained", "under_constrained")
