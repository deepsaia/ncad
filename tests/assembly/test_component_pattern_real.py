import json
import os

import pytest

pytestmark = pytest.mark.slow

_PART = '''schema_version = 2
units = mm
parts {
  plate { profile = solid,
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 60, h = 60 } ] },
      { id = ext, op = extrude, profile = sk, distance = 5 } ] }
  peg { profile = solid,
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = c, type = circle, d = 6, at = [ 20, 0 ] } ] },
      { id = ext, op = extrude, profile = sk, distance = 8 } ] }
}'''

_ASM = '''schema_version = 1
units = mm
assembly {
  instances = [
    { id = base, file = "p.hocon", part = plate, lock = true }
    { id = peg, file = "p.hocon", part = peg,
      pattern = { kind = circular, count = 4, axis = { point = [0,0,0], dir = [0,0,1] } } }
  ]
}'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_component_pattern_places_four_pegs(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    asm = _write(str(tmp_path), "a.asm.hocon", _ASM)
    result = AssemblyBuilder(Build123dKernel()).assemble(asm, str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "a.assembly.json").read_text())
    ids = {i["id"] for i in sidecar["instances"]}
    assert {"peg/0", "peg/1", "peg/2", "peg/3"} <= ids
