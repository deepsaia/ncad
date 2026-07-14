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
        elements = [ { id = r, type = rectangle, w = 80, h = 40 } ] },
      { id = ext, op = extrude, profile = sk, distance = 5 } ] }
  bracket { profile = solid,
    features = [
      { id = sk, op = sketch, plane = XY,
        elements = [ { id = r, type = rectangle, w = 10, h = 10 } ] },
      { id = ext, op = extrude, profile = sk, distance = 12 } ] }
}'''

_ASM = '''schema_version = 1
units = mm
assembly {
  instances = [
    { id = base, file = "p.hocon", part = plate, lock = true }
    { id = leftBracket, file = "p.hocon", part = bracket, placement = { position = [25, 0, 5] } }
    { id = rightBracket, of = leftBracket, mirror = { plane = YZ } }
  ]
}'''


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_component_mirror_reflects_to_negative_x(tmp_path):
    from ncad.assembly.assembly_builder import AssemblyBuilder
    from ncad.kernel.build123d_kernel import Build123dKernel

    _write(str(tmp_path), "p.hocon", _PART)
    asm = _write(str(tmp_path), "a.asm.hocon", _ASM)
    result = AssemblyBuilder(Build123dKernel()).assemble(asm, str(tmp_path))
    assert not result["issues"], result["issues"]
    sidecar = json.loads((tmp_path / "a.assembly.json").read_text())
    right = next(i for i in sidecar["instances"] if i["id"] == "rightBracket")
    # The mirrored bracket sits at -x (placement baked to metres: 25 mm -> -0.025 m).
    assert right["placement"][3][0] < 0.0
